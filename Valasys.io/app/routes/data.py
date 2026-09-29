import csv
import base64
import io
import json
import re
import uuid
from datetime import datetime, timedelta, timezone
from math import ceil
from urllib.parse import quote

from bson import ObjectId
from bson.decimal128 import Decimal128
from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse, Response
from fastapi.templating import Jinja2Templates
from openpyxl import Workbook
from pymongo.collation import Collation

from app.database.mongodb import (
    get_company_collection,
    get_company_csv_filter_collection,
)


router = APIRouter()

templates = Jinja2Templates(
    directory="app/templates"
)

MAX_CSV_DATA_ROWS = 1000
MAX_EXPORT_COMPANIES = 1000
CSV_FILTER_TTL = timedelta(hours=2)


def normalize_export_value(value):
    if isinstance(value, ObjectId):
        return str(value)
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, Decimal128):
        return str(value)
    if isinstance(value, bytes):
        return base64.b64encode(value).decode("ascii")
    if isinstance(value, dict):
        return {
            key: normalize_export_value(item)
            for key, item in value.items()
        }
    if isinstance(value, (list, tuple)):
        return [normalize_export_value(item) for item in value]
    return value


def export_cell_value(value):
    value = normalize_export_value(value)
    if isinstance(value, (dict, list)):
        value = json.dumps(value, ensure_ascii=False)
    if isinstance(value, str) and value.lstrip(" \t\r\n")[:1] in "=+-@":
        return "'" + value
    return value


def parse_company_ids(values):
    if not isinstance(values, list) or len(values) > MAX_EXPORT_COMPANIES:
        raise HTTPException(status_code=400, detail="Invalid company selection.")
    if any(not isinstance(value, str) or len(value) > 128 for value in values):
        raise HTTPException(status_code=400, detail="Invalid company selection.")
    return [ObjectId(value) if ObjectId.is_valid(value) else value for value in values]


@router.post("/companies/export")
async def export_companies(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Authentication required.")

    try:
        payload = await request.json()
    except (ValueError, json.JSONDecodeError):
        raise HTTPException(status_code=400, detail="Invalid export request.")

    if not isinstance(payload, dict) or payload.get("format") not in {"xlsx", "json", "csv"}:
        raise HTTPException(status_code=400, detail="Choose a supported export format.")

    selection = payload.get("selection")
    if not isinstance(selection, dict):
        raise HTTPException(status_code=400, detail="Invalid company selection.")

    if selection.get("all") is True:
        excluded_ids = parse_company_ids(selection.get("excludedIds", []))
        query = {"_id": {"$nin": excluded_ids}} if excluded_ids else {}
        companies = list(
            get_company_collection()
            .find(query)
            .sort("Company_Name", 1)
            .limit(MAX_EXPORT_COMPANIES)
        )
    else:
        company_ids = parse_company_ids(selection.get("ids", []))
        if not company_ids:
            raise HTTPException(status_code=400, detail="Select at least one company.")
        companies = list(
            get_company_collection()
            .find({"_id": {"$in": company_ids}})
            .sort("Company_Name", 1)
        )

    if not companies:
        raise HTTPException(status_code=404, detail="No selected companies were found.")

    columns = list(dict.fromkeys(
        key for company in companies for key in company
    ))
    file_format = payload["format"]

    if file_format == "json":
        content = json.dumps(
            normalize_export_value(companies),
            ensure_ascii=False,
            indent=2,
        ).encode("utf-8")
        media_type = "application/json"
    elif file_format == "csv":
        output = io.StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(columns)
        for company in companies:
            writer.writerow([
                export_cell_value(company.get(column))
                for column in columns
            ])
        content = output.getvalue().encode("utf-8-sig")
        media_type = "text/csv; charset=utf-8"
    else:
        workbook = Workbook(write_only=True)
        worksheet = workbook.create_sheet("Companies")
        worksheet.append(columns)
        for company in companies:
            worksheet.append([
                export_cell_value(company.get(column))
                for column in columns
            ])
        output = io.BytesIO()
        workbook.save(output)
        content = output.getvalue()
        media_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    filename = f"companies_{datetime.now(timezone.utc):%Y%m%d_%H%M%S}.{file_format}"
    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def csv_filter_error(message: str):
    return RedirectResponse(
        f"/companies?csv_error={quote(message)}",
        status_code=303
    )


@router.post(
    "/companies/csv-filter",
    response_class=HTMLResponse
)
async def create_company_csv_filter(
    request: Request,
    file: UploadFile = File(...)
):

    user = request.session.get("user")

    if not user:
        return RedirectResponse(
            "/",
            status_code=303
        )

    if not file.filename or not file.filename.lower().endswith(".csv"):
        return csv_filter_error("Choose a .csv file.")

    try:
        content = await file.read()
        text = content.decode("utf-8-sig")
        reader = csv.reader(io.StringIO(text))
        headers = next(reader, None)

        if not headers:
            return csv_filter_error("The CSV file is empty.")

        headers = [header.strip() for header in headers]

        if any(not header for header in headers):
            return csv_filter_error(
                "Every column must have a header in the first row."
            )

        normalized_headers = [header.casefold() for header in headers]

        if len(set(normalized_headers)) != len(normalized_headers):
            return csv_filter_error("Column headers must be unique.")

        filter_columns = [
            (index, header.casefold())
            for index, header in enumerate(headers)
            if header.casefold() in {"companies", "website"}
        ]

        if len(filter_columns) != 1:
            return csv_filter_error(
                "CSV must contain exactly one column named Companies or Website."
            )

        value_index, header_name = filter_columns[0]
        filter_field = (
            "Company_Name" if header_name == "companies" else "Website"
        )
        filter_label = "Companies" if header_name == "companies" else "Website"
        values = []
        row_count = 0

        for row in reader:
            if not any(value.strip() for value in row):
                continue

            row_count += 1
            if row_count > MAX_CSV_DATA_ROWS:
                return csv_filter_error(
                    "The CSV file cannot contain more than 1,000 rows."
                )

            if value_index < len(row) and row[value_index].strip():
                values.append(row[value_index].strip())

    except (UnicodeDecodeError, csv.Error):
        return csv_filter_error("The CSV file could not be read.")

    values = list(dict.fromkeys(values))

    if not values:
        return csv_filter_error(
            f"The {filter_label} column does not contain any values."
        )

    now = datetime.now(timezone.utc)
    filter_id = uuid.uuid4().hex
    filter_collection = get_company_csv_filter_collection()
    filter_collection.create_index("expires_at", expireAfterSeconds=0)
    filter_collection.delete_many({"expires_at": {"$lte": now}})
    filter_collection.insert_one(
        {
            "token": filter_id,
            "user_email": user.get("email"),
            "field": filter_field,
            "label": filter_label,
            "values": values,
            "expires_at": now + CSV_FILTER_TTL,
        }
    )

    return RedirectResponse(
        f"/companies?csv_filter={filter_id}",
        status_code=303
    )


@router.get(
    "/prospects",
    response_class=HTMLResponse
)
async def prospects(request: Request):

    user = request.session.get("user")

    if not user:
        return RedirectResponse(
            "/",
            status_code=303
        )

    return templates.TemplateResponse(
        "prospects.html",
        {
            "request": request,
            "user": user
        }
    )


@router.get(
    "/companies",
    response_class=HTMLResponse
)
async def companies(
    request: Request,
    page: int = 1,
    search: str = "",
    country: str = "",
    csv_filter: str = "",
    csv_error: str = ""
):

    user = request.session.get("user")

    if not user:
        return RedirectResponse(
            "/",
            status_code=303
        )


    # -----------------------------------------
    # Pagination
    # -----------------------------------------

    per_page = 25
    max_records = 1000

    if page < 1:
        page = 1


    collection = get_company_collection()
    csv_filter_id = ""
    csv_filter_label = ""
    csv_filter_document = None

    if csv_filter:
        csv_filter_document = get_company_csv_filter_collection().find_one(
            {
                "token": csv_filter,
                "user_email": user.get("email"),
                "expires_at": {"$gt": datetime.now(timezone.utc)},
            }
        )

        if csv_filter_document:
            csv_filter_id = csv_filter
            csv_filter_label = csv_filter_document["label"]
        else:
            csv_error = "The CSV filter expired. Upload the file again."


    # -----------------------------------------
    # Search filter
    # -----------------------------------------

    query = {}


    if search.strip():

        search_pattern = re.escape(search.strip())
        query["$or"] = [
            {
                "Company_Name": {
                    "$regex": search_pattern,
                    "$options": "i"
                }
            },
            {
                "Website": {
                    "$regex": search_pattern,
                    "$options": "i"
                }
            }
        ]


    # -----------------------------------------
    # Country filter
    #
    # Your current data uses:
    # Headquarter_Location
    #
    # Example:
    # "Redmond, Washington, USA"
    # -----------------------------------------

    if country.strip():

        query["Headquarter_Location"] = {
            "$regex": country.strip() + r"$",
            "$options": "i"
        }


    if csv_filter_document:
        if csv_filter_document["field"] == "Website":
            website_patterns = []

            for value in csv_filter_document["values"]:
                normalized_website = re.sub(
                    r"^https?://",
                    "",
                    value.strip(),
                    flags=re.IGNORECASE
                )
                normalized_website = re.sub(
                    r"^www\.",
                    "",
                    normalized_website,
                    flags=re.IGNORECASE
                ).rstrip("/")

                if normalized_website:
                    website_patterns.append(
                        re.compile(
                            r"^(?:https?://)?(?:www\.)?"
                            + re.escape(normalized_website)
                            + r"/?$",
                            re.IGNORECASE
                        )
                    )

            query.setdefault("$and", []).append(
                {
                    "Website": {
                        "$in": website_patterns
                    }
                }
            )
        else:
            query[csv_filter_document["field"]] = {
                "$in": csv_filter_document["values"]
            }


    # -----------------------------------------
    # Total records
    # -----------------------------------------

    query_options = {}
    if csv_filter_document:
        query_options["collation"] = Collation(locale="en", strength=2)

    total_companies = min(
        collection.count_documents(query, **query_options),
        max_records
    )


    total_pages = max(
        1,
        ceil(total_companies / per_page)
    )


    # Prevent invalid page number

    if page > total_pages:
        page = total_pages


    skip = (page - 1) * per_page


    # -----------------------------------------
    # Get current page
    # -----------------------------------------

    companies = list(
        collection
        .find(query, **query_options)
        .sort("Company_Name", 1)
        .skip(skip)
        .limit(per_page)
    )


    # -----------------------------------------
    # Countries
    # -----------------------------------------

    countries_cursor = collection.find(
        {},
        {
            "Headquarter_Location": 1
        }
    )


    countries = set()


    for item in countries_cursor:

        location = item.get(
            "Headquarter_Location",
            ""
        )

        if location:

            parts = [
                part.strip()
                for part in location.split(",")
                if part.strip()
            ]

            if parts:

                countries.add(
                    parts[-1]
                )


    countries = sorted(
        countries,
        key=lambda x: x.lower()
    )


    # -----------------------------------------
    # Showing range
    # -----------------------------------------

    if total_companies > 0:

        start_number = skip + 1

        end_number = min(
            skip + len(companies),
            total_companies
        )

    else:

        start_number = 0
        end_number = 0


    return templates.TemplateResponse(
        request,
        "companies.html",
        {
            "request": request,

            "user": user,

            "companies": companies,

            "company_count": total_companies,

            "current_page": page,

            "per_page": per_page,

            "total_pages": total_pages,

            "start_number": start_number,

            "end_number": end_number,

            "search": search,

            "selected_country": country,

            "countries": countries,

            "csv_filter_id": csv_filter_id,

            "csv_filter_label": csv_filter_label,

            "csv_error": csv_error
        }
    )