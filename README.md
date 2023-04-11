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

The plugin works for Calibre 4 and later.

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

[calibre-image]: https://img.shields.io/badge/calibre-4.00.0_and_above-green
[calibre-url]: https://www.calibre-ebook.com/

[status-image]: https://img.shields.io/badge/Status-Stable-green

[mobileread-image]: https://img.shields.io/badge/MobileRead-Plugin%20Thread-blue?logo=data:image/x-icon;base64,AAABAAEAEBAAAAEAIABoBAAAFgAAACgAAAAQAAAAIAAAAAEAIAAAAAAAQAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAns32/zqT5v8SeeD/Enng/xJ54P8SeeD/LYvl/3+78v8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAZazv/xJ54P8SeeD/Enng/zqT5v9Jm+n/HoLi/xJ54P8SeeD/OpPm/wAAAAAAAAAAAAAAAAAAAAAAAAAAzub7/xJ54P8SeeD/Enng/4/D9P/p6en/0tLS/8Tc8P8SeeD/Enng/xJ54P+Pw/T/AAAAAAAAAAAAAAAAAAAAAL3e+v8SeeD/Enng/xJ54P+93vr/Wlpa/zc3N/8AAAAAEnng/xJ54P8SeeD/f7vy/wAAAAAAAAAAAAAAAAAAAAAAAAAAHoLi/xJ54P8SeeD/T3+r/yQkJP9+jpz/Zazv/xJ54P8SeeD/Enng/73e+v8AAAAAAAAAAAAAAAAAAAAAz8Kt/66uof+Gj4L/ho+C/5SKb/+Vh2j/ho+C/4aPgv+Gj4L/ho+C/5OVgv+6qYP/yryi/wAAAAAAAAAAp5BW/6eQVv+nkFb/p5BW/6eQVv+nkFb/p5BW/6eQVv+nkFb/p5BW/6eQVv+nkFb/p5BW/6eQVv8AAAAA6ePb46eQVv+nkFb/p5BW/6eQVv+nkFb/xLWY/8/Crf/Pwq3/vq6N/7qogv+6qIL/uqiC/7qogv+nkFb/5uDW/+bg1v+nkFb/p5BW/6eQVv+nkFb/p5BW/+zn4f///////////8zMzP92dnb/VFRU/9nZ2f//////taJ5/8/Crf/m4Nb/p5BW/6eQVv+nkFb/p5BW/6eQVv/m4Nb////////////MzMz/k5OT/8zMzP/z8/P//////8S1mP/EtZj/5uDW/6eQVv+nkFb/p5BW/6eQVv+nkFb/oZ6Z/5OTk//m5ub/////////////////8/Pz/3Z2dv9xcHD/j4h7/9rRwf+nkFb/p5BW/6eQVv+nkFb/VVNP/8zMzP/z8/P/dnZ2/9nZ2f///////////5OTk//z8/P//////3Rxa//Pwq3/p5BW/6eQVv+nkFb/p5BW/2FgYP///////////76+vv/MzMz///////////+ioqL/oqKi/76+vv91b2X/z8Kt/6eQVv+nkFb/p5BW/6eQVv+JfWX/bGtq/4WFhf+FhYX//////////////////////76+vv++vr7/taJ5/8/Crf+nkFb/p5BW/6eQVv+nkFb/p5BW/8m7ov//////+Pb1/+bg1v/g2Mz/z8Kt/8/Crf+6qIL/uqiC/6eQVv/m4Nb/uqmD/7qpg/+nkFb/p5BW/6eQVv+nkFb/rZZh/7qpg/+/r43/z8Kt/8/Crf/m4NYd5uDWVQAAAAAAAAAA8A8AAOAHAADAAwAAwEMAAOADAADAAQAAgAEAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAMAAA==