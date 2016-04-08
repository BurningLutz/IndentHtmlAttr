import sublime, sublime_plugin
import re
import math

def _get_setting(key, default=None):
  settings = sublime.load_settings("IndentHtmlAttr.sublime-settings")
  return settings.get(key, default)

def normed_indentation(view, r, tab_size):
    pos = 0
    ln = view.line(r)

    for pt in range(ln.begin(), r.begin()):
        ch = view.substr(pt)

        if ch == '\t':
            pos += tab_size - (pos % tab_size)
        else:
            pos+=1

    return pos

class IndentHtmlAttrCommand(sublime_plugin.TextCommand):
  def __init__(self, view):
    super(IndentHtmlAttrCommand, self).__init__(view)

    sp_char = " \u0009\u000a\u000c\u000d"
    ctrl_char = "\u0000-\u001f\u007f-\u009f"
    attr_name = "[^{sp_char}{ctrl_char}\"'>/=]".format(sp_char=sp_char, ctrl_char=ctrl_char)
    attr_pattern = "[{sp_char}]+(({attr_name}+)([{sp_char}]*=[{sp_char}]*(\"[^\"]*\"|'[^']*'|[^{sp_char}\"'=<>`/]+))?)".format(attr_name=attr_name, sp_char=sp_char)
    self.attr_pattern = re.compile(attr_pattern)
    attrs_pattern = "({attr_pattern})+".format(attr_pattern=attr_pattern) # tags with no attributes will not be considered.
    self.attrs_pattern = re.compile(attrs_pattern)

    tag_name = "[a-zA-Z0-9]"
    tag_pattern = "(<(?!/)({tag_name}+:{tag_name}+|({tag_name}+\-)*{tag_name}+){attrs_pattern}[{sp_char}]*/?>)".format(tag_name=tag_name, attrs_pattern=attrs_pattern, sp_char=sp_char)
    self.tag_pattern = tag_pattern

  def run(self, edit):
    current_syntax = self.view.settings().get("syntax")
    allowed_syntaxes = _get_setting("allowed_syntaxes")
    if all(map(lambda s: current_syntax.upper().find(s.upper()) == -1, allowed_syntaxes)): # do nothing if syntax not matched.
      return

    start_tags = self.view.find_all(self.tag_pattern)
    start_tags.reverse()
    ceiling = _get_setting("indent_ceiling")
    for r in start_tags:
      if r.b - r.a <= ceiling:
        continue

      start_tag = self.view.substr(r)
      start_tag_without_attr = self.attrs_pattern.sub("", start_tag)
      attr_start_from = self.attrs_pattern.search(start_tag).start()

      attrs_found = self.attr_pattern.findall(start_tag)
      attrs = [i[0] for i in attrs_found]
      attrs.insert(0, "")

      tab_size = self.view.settings().get("tab_size")
      col = normed_indentation(self.view, r, tab_size)
      white_space = "\n" + "\t"*int(math.floor(float(col)/float(tab_size)) + 1)

      new_start_tag = start_tag_without_attr[:attr_start_from] + white_space.join(attrs) + start_tag_without_attr[attr_start_from:]

      self.view.replace(edit, r, new_start_tag)

class IndentHtmlAttrOnSave(sublime_plugin.EventListener):
  def on_pre_save(self, view):
    indent_on_save = _get_setting("indent_on_save")

    if indent_on_save:
      view.run_command("indent_html_attr")
