import sqlite3 as sql
from typing import List
import sys
import os

class Arg:
    def __init__(self, name, desc, default=None):
        self.name = name
        self.desc = desc
        self.default = default

class Option:
    def __init__(self, name, cb, args=[]):
        self.name = name
        self.cb = cb
        self.args = args

class View:
    def __init__(self, name, options: List[Option]):
        self.name = name
        self.options = options

    def execute(self, option_id):
        args = {}
        if option_id >= len(self.options):
            raise Exception("Please enter a valid option")
        option = self.options[option_id]
        if len(option.args):
            for arg in option.args:
                val = None
                if not arg.default is None:
                    val = arg.default
                else:
                    val = input(f"{arg.desc}: ")
                args[arg.name] = val
        if option.cb:
            option.cb(**args)
    
    def __repr__(self):
        out = f"{self.name}\n"
        for i, option in enumerate(self.options):
            out += f"[{i + 1}] - {option.name}\n"
        return out

class Note:
    def __init__(self, name, desc, id):
        self.name = name
        self.desc = desc
        self.id = id


class NotesView(View):
    def __init__(self, notes, view_note):
        options = [
                Option(
                    name=note.name, 
                    cb=view_note, 
                    args=[
                        Arg(name="note", desc=None, default=note),
                        ])
                    for note in notes
            ]
        super().__init__(name="Notes", options=options)

class NoteView(View):
    def __init__(self, note):
        self.note = note
        super().__init__(name=note.name, options=[])
    def __repr__(self):
        return f"name: {self.note.name}\ndescription: {self.note.desc}\nid: {self.note.id}"

class Program:
    def __init__(self):
        '''
        [1] - View notes
        [2] - Add note
        [3] - Delete note
        [4] - Edit note
        [5] - Exit
        '''
        if not os.path.exists("sqlite.db"):
            # create the schema
            with open("schema.sql") as file:
                script = file.read()
            con = sql.connect("sqlite.db")
            con.executescript(script)
            con.close()

        self.con = sql.connect("sqlite.db")
        self.view_stack = []
        self.goto(View(
            name="Main Menu",
            options=[
                Option(name="View notes", cb=self.view_notes),
                Option(name="Add note", cb=self.add_note, args=[Arg("name", "note name"), Arg("desc", "description")]),
                Option(name="Delete note", cb=self.delete_note, args=[Arg("id", "note id")]),
                ]
            ))

    def goto(self, view):
        self.view_stack.append(view)

    def view_notes(self):
        cur = self.con.cursor()
        result = cur.execute("select rowid, name, description from Note")
        notes = []
        for note in result.fetchall():
            notes.append(Note(name=note[1], desc=note[2], id=note[0]))
        cur.close()
        self.goto(NotesView(notes=notes, view_note=self.view_note))

    def view_note(self, note):
        self.goto(NoteView(note))

    def add_note(self, name, desc):
        cur = self.con.cursor()
        cur.execute("insert into Note (name, description) values (?, ?)", (name, desc))
        self.con.commit()
        cur.close()

    def delete_note(self, id):
        cur = self.con.cursor()
        cur.execute("delete from Note where rowid = ?", (id,))
        self.con.commit()
        cur.close()

    def get_option(self):
        o = input("Enter option [b - back]: ")
        return o

    def loop(self):
        prev_err = None

        while True:
            if not self.view_stack:
                self.exit()
            os.system("clear")
            if prev_err:
                print(prev_err)
            print(self.view_stack[-1])
            option = self.get_option()
            if option == 'b':
                self.view_stack.pop()
                if not self.view_stack:
                    self.exit()
                continue
            try:
                option = int(option) - 1
                self.view_stack[-1].execute(option)
            except:
                prev_err = "Please enter a valid option: "
                continue
            prev_err = None

    def exit(self):
        self.con.close()
        sys.exit(0)

if __name__ == "__main__":
    p = Program()
    try:
        p.loop()
    except Exception as e:
        print(e)
        p.exit()
