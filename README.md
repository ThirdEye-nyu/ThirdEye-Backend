# NYU DevOps Project - Wishlists

[![Build Status](https://github.com/CSCI-GA-2820-FA22-001/wishlists/actions/workflows/ci.yml/badge.svg)](https://github.com/CSCI-GA-2820-FA22-001/wishlists/actions)

[![License](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![Python](https://img.shields.io/badge/Language-Python-blue.svg)](https://python.org/)


## Overview

Following is the project setup for the Wishlists functionality of a demo e-commerce website. It allows for creation of multiple wishlists for each customer and multiple items with fields like `rank, quantity, price` for various functionality. The service supports all CRUD: create, read, update, delete, list and find by query operations on the main schemas of `Wishlist` and `Items` which correspond to the Items list in a wishlist.

## Available REST API's

Route | Operation | Description
-- | -- | --
/healthcheck | | Service Healthcheck
/ | root index | Root URL returns service name
POST /wishlists | CREATE | Create new Wishlist
GET /wishlists/`<wishlist_id>` | READ | Show a single wishlist
POST /wishlists/`<wishlist_id>`/items | CREATE | Add item in body to wishlist
GET /wishlists/`<wishlist_id>`/items/`<item_id>` | READ | Show a given item in wishlist
DELETE /wishlists/`<wishlist_id>` | DELETE | Delete given Wishlist
DELETE /wishlists/`<wishlist_id>`/items/`<item_id>` | DELETE | Delete item from Wishlist
PUT /wishlists/`<id>` | UPDATE | Rename wishlist
GET /wishlists/`<id>`/items | READ | List items in wishlist [ordered by rank field]
GET /wishlists | LIST | Show all wishlists
GET /wishlists?q=querytext | QUERY | Search for a wishlist
GET /wishlists/`<id>`?q=querytext | QUERY | Search for items in wishlist


## Running the service

Given that you have cloned the repository. Using the below command in the repo folder:
``` text
$ code .
```
opens the repo in VSCode, where you need to select the option to `Reopen in Containers` which brings up the `wishlist:app` and `postgres` images.

The project uses honcho which gets it's commands from the `Procfile`. To start the service simply use:
``` text
$ honcho start
```
You should be able to reach the service at: http://localhost:8000. The port that is used is controlled by an environment variable defined in the .flaskenv file which Flask uses to load it's configuration from the environment by default. Going to the above URL localhost:8000, you will see a message about the service which looks something like this:
``` text
{
  "name": "Wishlists Demo REST API Service", 
  "paths": "http://localhost:8000/wishlists", 
  "version": "1.0"
}
```
which is the response from the root index.
Other API routes can be hit as detailed from the `Available REST API's tab` which can be hit using `POSTMAN` or `curl` commands from terminal the POST API required a body of Wishlist or Items for creating them which looks like: 

## Wishlist model
``` text
{   "id": Int,
    "name": String,
    "customer_id": Int,
    "created_on": DateTime} 
```

## Items model
``` text
{   "id": Int,
    "name": String,
    "wishlist_id": Int,
    "product_id": Int,
    "created_on": DateTime,
    "rank": Int,
    "price": Int,
    "quantity": Int,
    "updated_on": DateTime} 
```


## Testing

The testing files are all present in app/tests folder. You can run the tests using: 

```text
nosetests
```
You will see all the tests passsing with the code coverage at the end. `setup.cfg` file controls test results level of detail like verbosity.

## Contents

The project contains the following:

```text
.gitignore          - this will ignore .devcontainer and other metadata files
.flaskenv           - Environment variables to configure Flask
.gitattributes      - File to gix Windows CRLF issues
.devcontainers/     - Folder with support for VSCode Remote Containers
dot-env-example     - copy to .env to use environment variables
requirements.txt    - list if Python libraries required by your code
config.py           - configuration parameters

service/                   - service python package
├── __init__.py            - package initializer
├── models.py              - module with business models
├── routes.py              - module with service routes
└── common                 - common code package
    ├── error_handlers.py  - HTTP error handling code
    ├── log_handlers.py    - logging setup code
    └── status.py          - HTTP status constants

tests/              - test cases package
├── __init__.py     - package initializer
├── test_wishlists_models.py  - test suite for Wishlist model
├── test_item_models.py  - test suite for Items model
└── test_routes.py  - test suite for service routes
```

## License

Copyright (c) John Rofrano. All rights reserved.

Licensed under the Apache License. See [LICENSE](LICENSE)

This repository is part of the NYU masters class: **CSCI-GA.2820-001 DevOps and Agile Methodologies** created and taught by *John Rofrano*, Adjunct Instructor, NYU Courant Institute, Graduate Division, Computer Science, and NYU Stern School of Business.
