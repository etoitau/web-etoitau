to do before push to production:
run 'python manage.py collectstatic' in the terminal

when models change
1. Run 'python manage.py makemigrations' to generate scripts in the migrations folder that migrate the database from its current state to the new state.
2. Run 'python manage.py migrate' to apply the scripts to the actual database.