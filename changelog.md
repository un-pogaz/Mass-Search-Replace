# Changelog - Mass Search/Replace

## [1.7.6] - date

### Changed
- Drop Python 2 / Calibre 4 comatibility, only 5 and above

## [1.7.5] - 2023/10/07

### Bug fixes
- Fix NotImplementedError: set() cannot be used in this context. ProxyMetadata is read only

## [1.7.4] - 2023/09/31

### Bug fixes
- Don't update the config file when Calibre start

## [1.7.3] - 2023/05/31

### Bug fixes
- Fix columns list not the same as Calibre

## [1.7.2] - 2023/04/12

### Bug fixes
- Fix active statue of Shared Search/Replace operation not conserved (always active)

## [1.7.1] - 2023/02/03

### Bug fixes
- Fix broken compatibility with 6.12 (use a icon instead of a red border to warn about a regex error)

## [1.7.0] - 2022/10/19

### Changed
- Again, big rework of common_utils (use submodule)

## [1.6.1] - 2022/10/17

### Bug fixes
- Fix a error when a user categorie exist in the library

## [1.6.0] - 2022/10/11

### Changed
- Big rework of common_utils.py

## [1.5.1] - 2022/09/08

### Bug fixes
- Fix a bug where the books are marked, even if an error has occurred in restore books
- Icon not display when a theme colors is used

## [1.5.0] - 2022/08/17

### Changed
- Rework of the Quick Search/Replace for add alternatives range target (Selection / Current Search / Virtual library / Library)

## [1.4.5] - 2022/08/06

### Changed
- Improvement of the 'Replace Field' mode

## [1.4.4] - 2022/07/20

### Changed
- Small incompatibility Calibre6/Qt6

## [1.4.3] - 2022/07/11

### Changed
- More compatibility Calibre6/Qt6

## [1.4.2] - 2022/03/11

### Changed
- Small improvement for identifier operation

## [1.4.1] - 2022/02/25

### Bug fixes
- Calibre Search/Replace operation are not saved if it contains an error

## [1.4.0] - 2022/02/25

### Added
- Shared Search/Replace operation: set in once, used where you want, edit them and all reference has edited<br>Uses and compatible with Calibre saved Search/Replace system

## [1.3.3] - 2022/02/24

### Bug fixes
- Fix the fix of Calibre saved Search/Replace operation

## [1.3.2] - 2022/02/23

### Bug fixes
- The Calibre saved Search/Replace operation could not be loaded

## [1.3.1] - 2022/02/22

### Changed
- Various technical improvement

## [1.3.0] - 2022/01/04

### Changed
- Compatible Calibre6/Qt6

## [1.2.2] - 2021/07/01

### Bug fixes
- Fix wrong error message when an error occurs during the update of the library

## [1.2.1] - 2021/06/08

### Bug fixes
- Fix ghost identifier with empty value

## [1.2.0] - 2021/05/28

### Added
- Add a 'Replace Field' mode that replace any values with the specified string

### Bug fixes
- Fix freeze when your config the settings of operations when many books are selected
- Fix the displaying of a error in dialog

## [1.1.0] - 2021/05/25

### Bug fixes
- Improved handling of errors with invalid identifiers

## [1.0.2] - 2021/05/16

### Bug fixes
- Fix invalide identifier with colon

## [1.0.1] - 2021/02/12

### Bug fixes
- Fix error in search mode "Character match"

## [1.0.0] - 2021/01/18

### Full release

### Bug fixes
- Fix regression with case sensitivity

## [0.9.3] - 2020/12/08

### Added
- Add Spanish translation. Thanks *dunhill*

## [0.9.2] - 2020/12/08

### Bug fixes
- Fix case for the test result field
- Fix detection of None and inchanged value

## [0.9.1] - 2020/12/07

### Bug fixes
- Fix library switch

## [0.9.0] - 2020/12/06

### First release
- Beta public test
