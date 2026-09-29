document.addEventListener(
    "DOMContentLoaded",
    function () {

        const form =
            document.getElementById("loginForm");

        const email =
            document.getElementById("email");

        const password =
            document.getElementById("password");

        const emailError =
            document.getElementById("emailError");

        const passwordError =
            document.getElementById("passwordError");

        const togglePassword =
            document.getElementById(
                "togglePassword"
            );

        const loginButton =
            document.getElementById(
                "loginButton"
            );

        const buttonText =
            document.getElementById(
                "buttonText"
            );


        /* Password visibility */

        togglePassword.addEventListener(
            "click",
            function () {

                if (
                    password.type ===
                    "password"
                ) {

                    password.type =
                        "text";

                    togglePassword.textContent =
                        "Hide";

                } else {

                    password.type =
                        "password";

                    togglePassword.textContent =
                        "Show";
                }

            }
        );


        /* Form validation */

        form.addEventListener(
            "submit",
            function (event) {

                let valid = true;

                emailError.textContent = "";
                passwordError.textContent = "";


                const emailValue =
                    email.value.trim();

                const passwordValue =
                    password.value;


                const emailPattern =
                    /^[^\s@]+@[^\s@]+\.[^\s@]+$/;


                if (
                    !emailPattern.test(
                        emailValue
                    )
                ) {

                    emailError.textContent =
                        "Please enter a valid email address.";

                    valid = false;
                }


                if (
                    passwordValue.length < 8
                ) {

                    passwordError.textContent =
                        "Password must contain at least 8 characters.";

                    valid = false;
                }


                if (!valid) {

                    event.preventDefault();

                    return;
                }


                loginButton.disabled = true;

                buttonText.textContent =
                    "Signing in...";
            }
        );

    }
);