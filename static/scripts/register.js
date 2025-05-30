function validate_input(event) {
            const password = document.querySelector('#password').value;
            const confirm = document.querySelector('#confirm').value;
            const username = document.querySelector('#username').value;

            if (password !== confirm) {
                event.preventDefault();
                alert("Password and Confirmation not match!");
            }
            else if (password.toLowerCase() === username.toLowerCase()) {
                event.preventDefault();
                alert("Password can not be the same as Username!");
            }
        }

        document.addEventListener('DOMContentLoaded', function() {
            document.querySelector('form').addEventListener('submit', validate_input);
        });
