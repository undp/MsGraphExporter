# Changelog

## 0.1.0-rc.4 (2019-10-09)

### Changes

* `pytest` scripts discovery (fixes #11). [OK-UNDP]

### Fix

* Correct versioning in PyPI (fixes #12). [OK-UNDP]

## 0.1.0-rc.3 (2019-09-30)

### New

* Add Azure pipeline (fixes #8). [OK-UNDP]

### Changes

* Take creds from ENV vars (fixes #9). [OK-UNDP]

* Time-domain query method. (fixes #7). [OK-UNDP]

### Fix

* Add dev versions to PyPI (fixes #10). [OK-UNDP]

## 0.1.0-rc.2 (2019-09-13)

### New

* Publish docs on RTD (fixes #5). [OK-UNDP]

  Provide `.readthedocs.yaml` for RTD build environment.

  Change `description` in `pyproject.toml` to single-line format to address sdispater/poetry#1372

  Apply minor doc fixes.

### Fix

* Gevent monkey patching (fixes #6). [OK-UNDP]

  Ensure `gevent` monkey patching is performed
  only for tests requiring it.

* Read-only docker image (fixes #4). [OK-UNDP]

  Ensure all PID files are placed in `/tmp`. Provide an example
  `docker-compose.yaml` demonstrating how to deploy workers as
  read-only images with `tmpfs` volume mounted to `/tmp`.

* Empty `app_config.yaml` (fixes #3). [OK-UNDP]

  Properly handle empty or comments-only `app_config.yaml`.

* MsGraphResponse iterator (fixes #2). [OK-UNDP]

  Refactoring that allows `MsGraphResponse` to be repeatedly iterated.

## 0.1.0-rc.1 (2019-08-29)

### New

* Implement Redis upload benchmarking. [OK-UNDP]

* Package app as docker container. [OK-UNDP]

* Implement distributed data extraction and processing. [OK-UNDP]

* Implement a base class for data processing tasks. [OK-UNDP]

* Implement functional test for MS Graph API. [OK-UNDP]

* Implement MS Graph API module. [OK-UNDP]
