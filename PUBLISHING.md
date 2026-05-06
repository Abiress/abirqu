# AbirQu Publishing Guide
Copyright 2026 Abir Maheshwari

## 1. PyPI Package Release
1. Update version number in `setup.py`
2. Build distribution: `python setup.py sdist bdist_wheel`
3. Upload to PyPI: `twine upload dist/*`
4. Verify: `pip install abirqu==<version>`

## 2. GitHub Release
1. Tag version: `git tag -a v<version> -m "Release v<version>"`
2. Push tag: `git push origin v<version>`
3. Create GitHub release with release notes and PyPI link

## 3. Authorship Requirements
All releases must list Abir Maheshwari as the sole author. Do not include "team" credits or collective attribution.