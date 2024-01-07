requirements:
	pipenv lock --clear
	pipenv install --dev
	pipenv run pre-commit install

requirements_arm64:
	pipenv lock --clear
	arch -arm64 pipenv install --dev
	pipenv run pre-commit install