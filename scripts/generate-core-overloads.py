import re
import sys

prop_fmt = r"""

    @overload
    def {func}(
        self: {takes}, limit: Literal[1], *,
        {params}
    ) -> One{make}Generator: ...
    @overload
    def {func}(
        self: {takes}, limit: Limit = None, *,
        {params}
    ) -> {make}Generator: ...
    @overload
    def {func}(
        self: {takes}s, limit: Literal[1], *,
        {params}
    ) -> One{make}Generator: ...
    @overload
    def {func}(
        self: {takes}s, limit: Limit = None, *,
        {params}
    ) -> {make}Generator: ...
    @overload
    def {func}(
        self: One{take}Generator, limit: Limit = None, *,
        {params}
    ) -> GeneratedGenerator[{takes}, {makes}]: ...
    @overload
    def {func}(
        self: {take}Generator, limit: None = None, *,
        {params}
    ) -> GeneratedGenerator[{takes}, {makes}]: ...
    {original}"""
list_fmt = r"""

    @overload
    def {func}(
        self: {takes}, limit: Literal[1], *,
        {params}
    ) -> One{make}Generator: ...
    @overload
    def {func}(
        self: {takes}, limit: Limit = None, *,
        {params}
    ) -> {make}Generator: ...
    {original}"""
regex = r"""
    \s* (?:@ \s* overload [\s\S]*?)?
    (?P<original>def \s+ (?P<func>[a-z_][a-z_0-9]*) \s* \( \s*
        self [^,]* , \s* limit [^,]* , \s* \* \s* , \s*
        (?P<params>[^)]+?) \s*
    \) \s* -> \s* Any \s* : \s*
        \# \s* (?P<takes>[^\s-]+?\.?(?P<take>[^\s.-]+))(?P<spec>[\+!]) \s*
        -> \s* (?P<makes>[^\s-]+?\.?(?P<make>[^\s.-]+)) \s* $)
"""

if len(sys.argv) > 1:
    path = sys.argv[1]
else:
    path = input('File: ')

def repl(m: re.Match) -> str:
    if m.group('spec') == '+':
        return prop_fmt.format(**m.groupdict())
    return list_fmt.format(**m.groupdict())

with open(path, 'r+') as f:
    text = f.read()
    text = re.sub(regex, repl, text, flags=re.X | re.M)
    f.seek(0, 0)
    f.truncate(len(text))
    f.write(text)
