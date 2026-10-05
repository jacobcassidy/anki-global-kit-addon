Anki Global Kit keeps user CSS customizations in this folder so they survive
add-on upgrades. Create or edit either of these files:

  editor-ui.css      Styles the editor interface around the note fields.
  editor-fields.css  Styles content inside the editable note fields.

Rules in these files are applied after the add-on's packaged defaults. You can
add only the CSS rules you want to change. Restart Anki after editing the files
to reload the styles.

To find this folder in Anki, open Tools > Anki Global Kit Settings... > Editor,
then click View Stylesheet in Editor Fields. Use Enable custom Editor fields
styles to turn editor-fields.css on or off. It is enabled by default.

You can also open Tools > Add-ons, select Anki Global Kit, and click View Files.
Then open the user_files folder.
