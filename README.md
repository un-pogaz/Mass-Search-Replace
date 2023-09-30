# Mass Search/Replace
[![MobileRead][mobileread-image]][mobileread-url]
[![History][changelog-image]][changelog-url]
[![License][license-image]][license-url]
[![calibre Version][calibre-image]][calibre-url]
[![Status][status-image]][status-image]


*Mass Search/Replace* is a small plugin to facilitate the execution of one or more of your favorite Search and Replace operations to your books metadata.

Each entry in the context menu will launch a list of Search/Replace operations that you have previously set up. Setting up an operation uses the Calibre Search and Replace module.

The plugin has the following features:

* Editable context menu
* Editables operations list
* Error Strategy
* Quick Search/Replace  on various range: Selection, Current Search, Virtual library, Library.
* Shared Search/Replace operation: set in once, used where you want, edit them and all reference has edited (compatible with Calibre saved Search/Replace system)

Available operation type:

* Character match
* Regular expression
* Replace field

To use a "Shared Search/Replace operation", create and save a operation in the Calibre combo box, or select one that already exist.
Important, don't edit any field after having select the "Shared operation" or the link will be broken. To edit a "Shared operation", it will have to be re-registered with the same name in the Calibre saved Search/Replace system.
Once the "Shared operation" corrrectly save, the name of this one will appear in operations list.


**Special Notes:**

* Uses the Calibre Search/Replace module.
* <span style="color:red">**You can destroy your library using this plugin.** Changes are permanent. There is no undo function. You are strongly encouraged to back up your library before proceeding.</span>


**Credits:**

* The icon dialog and the dynamic menus for chains are based on code from the Open With plugin by kiwidude.
* The Calibre Actions is based on code from the Favourites Menu plugin by kiwidude.
* The module editor is based on calibre editor function editor by Kovid Goyal.
* The Search and Replace Action is based on calibre's search and replace. (chaley and Kovid Goyal)
* Thanks to capink and its plugin [Action Chains](https://www.mobileread.com/forums/showthread.php?t=334974) without which this one wouldn't exist. 


**Installation**

Open *Preferences -> Plugins -> Get new plugins* and install the "Comments Cleaner" plugin.
You may also download the attached zip file and install the plugin manually, then restart calibre as described in the [Introduction to plugins thread](https://www.mobileread.com/forums/showthread.php?t=118680")

The plugin works for Calibre 5 and later.

Page: [GitHub](https://github.com/un-pogaz/Mass-Search-Replace) | [MobileRead](https://www.mobileread.com/forums/showthread.php?t=335417)

<ins>Note for those who wish to provide a translation:</ins><br>
I am *French*! Although for obvious reasons, the default language of the plugin is English, keep in mind that already a translation.


<br><br>

![configuration dialog of contextual menu](https://raw.githubusercontent.com/un-pogaz/Mass-Search-Replace/main/static/Mass_Search-Replace-config-menu.png)
![button contextual menu](https://raw.githubusercontent.com/un-pogaz/Mass-Search-Replace/main/static/Mass_Search-Replace-context.png)
![configuration dialog of a operations-list](https://raw.githubusercontent.com/un-pogaz/Mass-Search-Replace/main/static/Mass_Search-Replace-operations-list.png)
![configuration dialog for a Search/Replace operation](https://raw.githubusercontent.com/un-pogaz/Mass-Search-Replace/main/static/Mass_Search-Replace-config-operation.png)


[mobileread-url]: https://www.mobileread.com/forums/showthread.php?t=335417

[changelog-image]: https://img.shields.io/badge/History-CHANGELOG-blue.svg
[changelog-url]: changelog.md

[license-image]: https://img.shields.io/badge/License-GPL-yellow.svg
[license-url]: LICENSE

[calibre-image]: https://img.shields.io/badge/calibre-4.00.0_and_above-green?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAACXBIWXMAAA7DAAAOwwHHb6hkAAAAGXRFWHRTb2Z0d2FyZQB3d3cuaW5rc2NhcGUub3Jnm+48GgAAAllJREFUOMt1kz1MU1EUx3/3fZSP0lJLgVqRNqCDHxApAWcXF9O4oomDcXU06iIuLgxuTi4mrm7GRI2LiYOJ4ldAiBqxqSA2lEc/oNC+d991eI8HRnuGm3tzzv2d/znnXpEb5CHQDoCi8LigruHbrXOTs6Wl6qnkcPTd7SdvTvMfM/I1LgnhHYSgePHm9APheMAbV8e+mZoaR7BCCzMyEehNJXCky0bR2tJcdx7Nc+at0POjiQYokWkJABgcTlGv72AVLXRdQ9d0XKUob4uyF6aGWgE0gO36Jq7dBEBKl6Zt4zgO5bpe8uO6P768HGupACVRrvzHWdwMWbAFwHx96uy9u+UTc68WcmcuTCqljNzMFL80gCNDMfr6O0Eh9gOWq2YZsAFWGyNXYv3h6cLnyph0mllhMBGU8HVxleKKBQIFcKiv1y8HF1gG6NGXqqF2E8cGx3bQYSwA/Mxb1CrbQWYlwDT86iAPMGDMSYDIAcHGagUF4wEgnQ4Tj5t7AFehacLvssgDpPSFMGDH+kKUlssA2aCJ9a0GXV1GADBNA0e6u7g8gC4aaWBxMjc62tbeBpC6/oikBlCtNNmsNQKAbUtPvLf+8DcZJXgfTyYIxyLeCDWyGoAmFNWaDEYgpYNhmP49TwEQ6aT25a85Kx/QHVYkoq6fE1ylgnfhCrkLYDD0YW3/fQFZ7XsVXizAs3ko1Ij0J3pIpw5yOJkk3NHRefJ1egVoABw3nu4Ack8AWWM4yk7wnWHtd2k9Wiytt/kpLGbuuPcnRl27KRsDI/Fj6jxvhcBU8EkoZv8AURDxq1Vav0YAAAAASUVORK5CYII=
[calibre-url]: https://www.calibre-ebook.com/

[status-image]: https://img.shields.io/badge/Status-Stable-green

[mobileread-image]: https://img.shields.io/badge/MobileRead-Plugin%20Thread-blue?logo=data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABAAAAAQCAYAAAAf8/9hAAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAAsTAAALEwEAmpwYAAACJUlEQVQ4EZ3SX0hTYRjH8e+79DQcm5pGba0pQizrJhiMvJDwj3dR2SIoqK68CYouy24sb/TKbsuyC4kwG3gVBpUlqP1hBaUxiMp5aLZyzdn847E6+YQHDkNv+ty88PI8Px6e91XvJ5Nm9MU44t10GjuXplFV5qZIK6SyrARRHdgWAPbvqfT1A6jo8Buz73WcfAf3VnGqMczC4jKJbz9YWDJWzwxiIvkdMf41TQHrKE5P8XxgBP3lI0RraysiFKxAlA4NIRYNz/oBK3qcG7d7EEOrxbFYjFAohOjt7UX4/X5mYk9xlBe7yJf5mZMmcrkcg4ODuN1uLNlslubmZurq6tAcJv+W2DbwjHwNHgNjfo5IJILX68Uioe3t7RjGCq7tAQrYQG19E9UVXoRMMzY2Rk1NDcFgkM7OTq4/GEE42IBrs4adrut0dHSQTCYRiXSWrW4X6oOe0i9Hn/jJU79rpxQgJmcyzBu/sJMnbDtyAAVw/Npdk/9w78IJpVgjHyo385lEIo5Ir3hY/q3wObPYoblR5UEqyko43RhWCpupqwHzz2IO8Uqr5dKdCS6ePUkkME02FsXia+lHq2pQ9iVifHpsNQsOnzlPOBymu+8hpce6FTZLH4exFLBGOUuxM768pauri1QqRaBozpy9dQiLw1mCRWGTud9i2kfVfLvZ5CxmeXoCmc66850bVesGiIVYjzk7ehMjGceucMsO3PuO4mm6orD5CzQt1i+ddfLfAAAAAElFTkSuQmCC
