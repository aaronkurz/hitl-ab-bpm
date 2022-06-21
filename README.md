# HITL AB-BPM - Continuous, Rapid and Controllable Business Process Improvement
![Auto Updating Bagde](https://img.shields.io/endpoint?url=https://gist.githubusercontent.com/aaronkurz/1580622162fdac5e5c2571a4bf3cf13b/raw/pytest-coverage-comment__main.json)

HITL AB-BPM is a tool that allows for the structural A/B testing of business process models a business process management system with reinforcement learning techniques. As a machine might not have all information about the business process available to make the right choices, HITL AB-BPM allows human experts to be actively involved in the dynamic routing of instances to different process versions. Researchers can use the tool to explore new possibilities of joint human-machine decision-making for business process improvement and perspectively, practitioners can apply it to structure their process improvement.

![Screenshot](.github/hitl-ab-bpm-screenshot.png)

## Getting Started
### Setup
Instructions on how to run the app locally can be found in `source/README.md`.
### Usage
Learn more about how the app works in this [demo video](https://drive.google.com/file/d/1ikrVXHdGTwnV2HxRZLSaPFy9ZaTuM7pZ/view?usp=sharing).
### Development
To understand the code base better and get started with development, you can refer to the documentation.
For the backend, we have docstrings in the code and OpenAPI specs. More info on how to access the OpenAPI/SwaggerUI documentation can be found in `source/backend/README.md`.
The frontend is also documented using docstrings. All the docstrings follow the Python conventions for docstrings, so you could generate HTML documentation using tools like pdoc if needed.
## Structure
This repository contains the three main parts of the prototype: The backend, the frontend and the camunda engine with the [camunda-bpm-simulator](https://github.com/camunda-consulting/camunda-bpm-simulator).

For more info on the parts of the app, please refer to the READMEs in the sub-folders (`source/backend`, `source/frontend`, `api-tests`...).
We try to incorporate the READMEs at the spots where they are most relevant, in order to not add too much information here.

## Contributing

Whenever you encounter a :beetle: **bug** or have :tada: **feature request**, 
report this via Github issues.

### Git Commit Messages

Commits should start with a Capital letter and should be written in present tense (e.g. __:tada: Add cool new feature__ instead of __:tada: Added cool new feature__).
You should also start your commit message with **one** applicable emoji. This does not only look great but also makes you rethink what to add to a commit. Make many but small commits!

| Emoji                                                     | Description                                             |
|-----------------------------------------------------------|---------------------------------------------------------|
| :tada: `:tada:`                                           | When you added a cool new feature.                      |
| :wrench: `:wrench:`                                       | When you refactored / improved some code / added tests. |
| :sparkles: `:sparkles:`                                   | When you improved style.                                |
| :art: `:art:`                                             | When you improved / added assets like themes.           |
| :rocket: `:rocket:`                                       | When you improved performance.                          |
| :memo: `:memo:`                                           | When you wrote documentation.                           |
| :beetle: `:beetle:`                                       | When you fixed a bug.                                   |
| :twisted_rightwards_arrows: `:twisted_rightwards_arrows:` | When you merged a branch.                               |
| :fire: `:fire:`                                           | When you removed something.                             |
| :truck: `:truck:`                                         | When you moved / renamed something.                     |
