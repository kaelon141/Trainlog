# Trainlog

Online trips diary

## How to run the application

### Prerequisites
 - Python 3.14
 - [Git](https://git-scm.com/) and [Git LFS](https://git-lfs.com/) (If you intend to contribute on the project)
 - [Docker](https://docker.com) or [Podman](https://podman.io) (If you want to run the app in a container)
 - A [PostgreSQL](https://www.postgresql.org/) Database with the PostGIS extension enabled (if you want to run the app directly on your machine, rather than in a container.)

### Setup
First, copy the `.env.example` file and rename that file to `.env`, and then edit it with appropriate values.
If you intend to run the app in a container (easiest setup), you can leave the details as-is.
If you want the app to connect to a pre-existing PostgreSQL database, fill in the required details to connect to the database here.

Second, copy the `config-example.yaml` file and name it `config.yaml`, and open the file in your preferred text editor. The following sections need to be filled in:

- `pg`:
This section contains the login details for the PostgreSQL database. If you intend to run trainlog in a container, copy the login details from the `.env` file. 
Otherwise, fill in the details required for the app to connect to a pre-existing PostgreSQL database server.

- `owner`:

This section is for the application owner's details. When the app first runs, this account is created automatically as the site owner and is how you log in.
- `username`: Your preferred username.
- `email`: Your email address.
- `password`: Your password (will be securely hashed before storing).


With the essential configuration sections done, we can get to running Trainlog. There are two options for this.

### Option 1: In containers
Trainlog and its database can be ran as containers. This requires the least amount of setup. Trainlog supports both [Docker](https://www.docker.com/) and [Podman](https://podman.io/) as container engine.

#### Docker
Make sure you have both the `docker` and `docker-compose` packages installed (Linux), or that you have Docker Desktop installed (Windows, MacOS, or Linux).
If/once you do, simply run `docker compose up -d` in the project folder in order to build and run the project. This takes a few minutes the first time round to build the Trainlog project, and will be faster from there on. Once started, open the app by going to `http://localhost:5000` in your browser. You can stop the app by running `docker compose down` in the project folder.

If you make changes to the installed pip packages, run `docker compose down && docker compose up -d --build` to rebuild the project.

#### Podman
Make sure you have both the `podman` and `podman-compose` packages installed (Linux), or that you have Podman Desktop installed (Windows, MacOS).
If/once you do, simply run `podman compose up -d` in the project folder in order to build and run the project. This takes a few minutes the first time round to build the Trainlog project, and will be faster from there on. Once started, open the app by going to `http://localhost:5000` in your browser. You can stop the app by running `podman compose down` in the project folder.

If you make changes to the installed pip packages, run `podman compose down && podman compose up -d --build` to rebuild the project.

### Option 2: Manual installation

Install python dependencies:

```bash
pip install -r requirements.txt
```

If you want to use pyenv to manage your Python virtual environment, you can automatically enable
it for the trainlog folder with:

```bash
pyenv install 3.14
pyenv virtualenv 3.14 trainlog
pyenv local trainlog
pip install -r requirements.txt
```

Install pre-commit hooks, to automatically format and lint your code:

```bash
pre-commit install
```

Now, you can start the app by running `make start-local`.

## Configuration

Configuring the app is done by editing the `config.yaml` file. The file contains comments describing what each config section is for.

### Important Notes

- **Security**: Ensure that the `config.yaml` file is secured with the right file permissions and is not publicly accessible. Keep it out of version control to prevent accidentally exposing sensitive details.
- **Placeholder Configuration**: Do not use the `config-example.yaml` as is for the application. Always create a copy and provide real values.
- **Supported Python version**: Currently Python 3.13.x
