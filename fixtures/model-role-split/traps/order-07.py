

class TestSnowflakeListCommand(Validator):
    dialect = "snowflake"

    def test_list_command(self):
        with self.assertRaises(ParseError):
            parse_one("LIST @~", read="snowflake")
