program = parser.parse("private:x = 1", do_type_check=typecheck_flag, do_transform=True)
code = "private:x = 1\nprivate:x"
