# compile-requirements

Helper to validate and merge all nested requirements.txt files into a single requirements file.

`requirements.txt` supports nesting other files by using `-r other_requirements.txt`

This is particularly useful when a project includes multiple packages that can easily be removed, so the requirements from each package is specified within its directory.

When building docker images and using [multi stage builds](https://docs.docker.com/develop/develop-images/multistage-build/) this is an issue as it would require adding the whole context to the wheels building stage. That would invalidate the cache of that stage on every context change, even if all the requirements files remained the same.

One option was to duplicate the list of requirement files (already in the main file) to the Dockerfile, so only those were part of the cache. Other option was to flatten the requirements.txt, so the Dockerfile only had to copy one single `requirements.txt`.

*compile-requirements* aims to help with the second approach.

## Usage

Checks performed:
  - (Warning) package version is not pinned
  - (Fatal) package is duplicated with different versions
  - (Fatal) specific app requirements file missing from main file

Errors are printed to stderr; final requirement file is printed to stdout.  
Exit code not zero means at least a fatal check failed.

The script is built specifically for Python 3 & pip 20.1 (or higher) however the output can be used with any Python/pip version.

Usage example:

```
docker run --rm -v $(pwd)/:/app/:ro \
                   ghcr.io/surface-security//compile-requirements \
                   surface/requirements.txt > requirements_full.txt
```
