from rply.token import Token
from rply import ParserGenerator

from tokenizer import TOKENS, KEYWORDS, tokenize
from utils import create_node_from_token
from grammator_imports import include_imports
from grammator_control_structures import include_control_structures
from grammator_primitives import include_primivites
from grammator_operators import include_operators
from grammator_data_structures import include_data_structures


pg = ParserGenerator(tuple(map(lambda x: x.upper(), KEYWORDS)) + zip(*TOKENS)[1] + ("ENDMARKER", "INDENT", "DEDENT"), cache_id="baron")
        # precedence=[("left", ['PLUS', 'MINUS'])], cache_id="baron")


@pg.production("main : statements")
def main((statements,)):
    return filter(None, statements) if statements else []


@pg.production("statements : statements statement")
def statements_statement((statements, statement)):
    return statements + statement


@pg.production("statements : statement SEMICOLON?")
def statement((statement, semicolon)):
    if semicolon:
        return statement + [{"type": "semicolon", "value": ";"}]
    return statement


@pg.production("statement : endl")
def statement_endl((endl,)):
    return endl


@pg.production("endl : ENDL")
def endl((endl,)):
    return [{
        "type": "endl",
        "value": endl.value,
        "space": endl.before_space,
        "indent": endl.after_space,
    }]


@pg.production("endl : COMMENT ENDL")
def comment((comment_, endl)):
    return [{
        "type": "comment",
        "value": comment_.value,
        "space": comment_.before_space,
    }, {
        "type": "endl",
        "space": endl.before_space,
        "indent": endl.after_space,
        "value": endl.value
    }]


@pg.production("statement : ENDMARKER")
def end((endmarker)):
    return [None]


@pg.production("statement : simple_stmt")
@pg.production("statement : compound_stmt")
def statement_simple_statement((stmt,)):
    return stmt

@pg.production("simple_stmt : small_stmt SEMICOLON? endl")
def simple_stmt((small_stmt, semicolon, endl)):
    if semicolon:
        return [small_stmt, {"type": "semicolon", "value": ";", "before_space": semicolon.before_space, "after_space": semicolon.after_space}] + endl
    return [small_stmt] + endl


@pg.production("simple_stmt : small_stmt SEMICOLON simple_stmt")
def simple_stmt_semicolon((small_stmt, semicolon, simple_stmt)):
    return [small_stmt, {"type": "semicolon", "value": ";", "before_space": semicolon.before_space, "after_space": semicolon.after_space}] + simple_stmt


@pg.production("small_stmt : flow_stmt")
@pg.production("small_stmt : del_stmt")
@pg.production("small_stmt : pass_stmt")
@pg.production("small_stmt : assert_stmt")
@pg.production("small_stmt : raise_stmt")
@pg.production("small_stmt : global_stmt")
@pg.production("small_stmt : print_stmt")
@pg.production("compound_stmt : if_stmt")
@pg.production("compound_stmt : while_stmt")
@pg.production("compound_stmt : for_stmt")
@pg.production("compound_stmt : try_stmt")
@pg.production("compound_stmt : funcdef")
@pg.production("compound_stmt : classdef")
@pg.production("compound_stmt : with_stmt")
@pg.production("compound_stmt : decorated")
def small_and_compound_stmt((statement,)):
    return statement


@pg.production("small_stmt : expr_stmt")
@pg.production("expr_stmt : testlist")
@pg.production("testlist : test")
@pg.production("test : or_test")
@pg.production("test : lambdef")
@pg.production("or_test : and_test")
@pg.production("and_test : not_test")
@pg.production("not_test : comparison")
@pg.production("comparison : expr")
@pg.production("expr : xor_expr")
@pg.production("xor_expr : and_expr")
@pg.production("and_expr : shift_expr")
@pg.production("shift_expr : arith_expr")
@pg.production("arith_expr : term")
@pg.production("term : factor")
@pg.production("factor : power")
@pg.production("power : atom")
@pg.production("exprlist : expr")
def term_factor((level,)):
    return level


@pg.production("with_stmt : WITH with_items COLON suite")
def with_stmt((with_, with_items, colon, suite)):
    return [{
        "type": "with",
        "value": suite,
        "first_space": with_.after_space,
        "second_space": colon.before_space,
        "third_space": colon.after_space,
        "contexts": with_items
    }]


@pg.production("with_items : with_items comma with_item")
def with_items_with_item((with_items, comma, with_item,)):
    return with_items + [comma, with_item]


@pg.production("with_items : with_item")
def with_items((with_item,)):
    return [with_item]


@pg.production("with_item : test")
def with_item((test,)):
    return {
        "type": "with_context_item",
        "as": {},
        "first_space": "",
        "second_space": "",
        "value": test
    }


@pg.production("with_item : test AS expr")
def with_item_as((test, as_, expr)):
    return {
        "type": "with_context_item",
        "as": expr,
        "first_space": as_.before_space,
        "second_space": as_.after_space,
        "value": test
    }


@pg.production("classdef : CLASS NAME COLON suite")
def class_stmt((class_, name, colon, suite),):
    return [{
        "type": "class",
        "name": name.value,
        "parenthesis": False,
        "first_space": class_.after_space,
        "second_space": "",
        "third_space": "",
        "forth_space": "",
        "fith_space": "",
        "inherit_from": [],
        "value": suite,
    }]


@pg.production("classdef : CLASS NAME LEFT_PARENTHESIS RIGHT_PARENTHESIS COLON suite")
def class_stmt_parenthesis((class_, name, left_parenthesis, right_parenthesis, colon, suite),):
    return [{
        "type": "class",
        "name": name.value,
        "parenthesis": True,
        "first_space": class_.after_space,
        "second_space": left_parenthesis.before_space,
        "third_space": left_parenthesis.after_space,
        "forth_space": right_parenthesis.before_space,
        "fith_space": right_parenthesis.after_space,
        "inherit_from": [],
        "value": suite,
    }]


@pg.production("classdef : CLASS NAME LEFT_PARENTHESIS testlist RIGHT_PARENTHESIS COLON suite")
def class_stmt_inherit((class_, name, left_parenthesis, testlist, right_parenthesis, colon, suite),):
    return [{
        "type": "class",
        "name": name.value,
        "parenthesis": True,
        "first_space": class_.after_space,
        "second_space": left_parenthesis.before_space,
        "third_space": left_parenthesis.after_space,
        "forth_space": right_parenthesis.before_space,
        "fith_space": right_parenthesis.after_space,
        "inherit_from": [testlist],
        "value": suite,
    }]


@pg.production("decorated : decorators funcdef")
@pg.production("decorated : decorators classdef")
def decorated((decorators, funcdef)):
    funcdef[0]["decorators"] = decorators
    return funcdef


@pg.production("decorators : decorators decorator")
def decorators_decorator((decorators, decorator,)):
    return decorators + decorator


@pg.production("decorators : decorator")
def decorators((decorator,)):
    return decorator


@pg.production("decorator : AT dotted_name endl")
def decorator((at, dotted_name, endl)):
    return [{
        "type": "decorator",
        "value": {
            "value": dotted_name,
            "type": "dotted_name",
        },
        "call": {},
        "space": at.after_space,
    }] + endl


@pg.production("decorator : AT dotted_name LEFT_PARENTHESIS RIGHT_PARENTHESIS endl")
def decorator_empty_call((at, dotted_name, left_parenthesis, right_parenthesis, endl)):
    return [{
        "type": "decorator",
        "value": {
            "value": dotted_name,
            "type": "dotted_name",
        },
        "call": {
            "third_space": right_parenthesis.before_space,
            "type": "call",
            "first_space": left_parenthesis.before_space,
            "value": [],
            "second_space": left_parenthesis.after_space
        },
        "space": at.after_space,
    }] + endl


@pg.production("decorator : AT dotted_name LEFT_PARENTHESIS argslist RIGHT_PARENTHESIS endl")
def decorator_call((at, dotted_name, left_parenthesis, argslist, right_parenthesis, endl)):
    return [{
        "type": "decorator",
        "value": {
            "value": dotted_name,
            "type": "dotted_name",
        },
        "call": {
            "third_space": right_parenthesis.before_space,
            "type": "call",
            "first_space": left_parenthesis.before_space,
            "value": argslist,
            "second_space": left_parenthesis.after_space
        },
        "space": at.after_space,
    }] + endl


@pg.production("funcdef : DEF NAME LEFT_PARENTHESIS parameters RIGHT_PARENTHESIS COLON suite")
def function_definition((def_, name, left_parenthesis, parameters, right_parenthesis, colon, suite)):
    return [{
        "type": "funcdef",
        "decorators": [],
        "name": name.value,
        "first_space": def_.after_space,
        "second_space": left_parenthesis.before_space,
        "third_space": left_parenthesis.after_space,
        "forth_space": right_parenthesis.before_space,
        "fith_space": colon.before_space,
        "arguments": parameters,
        "value": suite,
    }]

@pg.production("argslist : argslist argument")
@pg.production("parameters : parameters parameter")
def parameters_parameters_parameter((parameters, parameter,),):
    return parameters + parameter

@pg.production("argslist : argument")
@pg.production("parameters : parameter")
def parameters_parameter((parameter,),):
    return parameter

@pg.production("argument :")
@pg.production("parameter : ")
def parameter_empty(p):
    return []

@pg.production("name : NAME")
def name((name_,)):
    return {
        "type": "name",
        "value": name_.value,
    }

@pg.production("argument : test")
@pg.production("parameter : name")
def parameter_one((name,)):
    return [{
        "type": "argument",
        "first_space": "",
        "second_space": "",
        "default": {},
        "value": name
    }]


@pg.production("parameter : LEFT_PARENTHESIS parameter RIGHT_PARENTHESIS")
def parameter_fpdef((left_parenthesis, parameter, right_parenthesis)):
    return [{
        "type": "associative_parenthesis",
        "first_space": left_parenthesis.after_space,
        "second_space": right_parenthesis.before_space,
        "value": parameter[0]
    }]


@pg.production("parameter : LEFT_PARENTHESIS fplist RIGHT_PARENTHESIS")
def parameter_fplist((left_parenthesis, fplist, right_parenthesis)):
    return [{
        "type": "argument",
        "first_space": "",
        "second_space": "",
        "default": {},
        "value": {
            "type": "tuple",
            "first_space": left_parenthesis.after_space,
            "second_space": right_parenthesis.before_space,
            "value": fplist
        }
    }]


@pg.production("fplist : fplist parameter")
def fplist_recur((fplist, parameter)):
    return fplist + parameter


@pg.production("fplist : parameter comma")
def fplist((parameter, comma)):
    return parameter + [comma]


# really strange that left part of argument grammar can be a test
# I guess it's yet another legacy mistake
# python give me 'SyntaxError: keyword can't be an expression' when I try to
# put something else than a name (looks like a custom SyntaxError)
@pg.production("argument : test EQUAL test")
def named_argument((name, equal, test)):
    return [{
        "type": "argument",
        "first_space": equal.before_space,
        "second_space": equal.after_space,
        "value": test,
        "name": name
    }]

@pg.production("parameter : name EQUAL test")
def parameter_with_default((name, equal, test)):
    return [{
        "type": "argument",
        "first_space": equal.before_space,
        "second_space": equal.after_space,
        "default": test,
        "value": name
    }]

@pg.production("argument : test comp_for")
def generator_comprehension((test, comp_for,)):
    return [{
        "type": "argument_generator_comprehension",
        "result": test,
        "generators": comp_for,
    }]

@pg.production("argument : STAR test")
def argument_star((star, test,)):
    return [{
        "type": "list_argument",
        "space": star.after_space,
        "value": test,
    }]

@pg.production("argument : DOUBLE_STAR test")
def argument_star_star((double_star, test,)):
    return [{
        "type": "dict_argument",
        "first_space": double_star.after_space,
        "second_space": double_star.after_space,
        "value": test,
    }]

# TODO refactor those 2 to uniformise with argument_star and argument_star_star
@pg.production("parameter : STAR NAME")
def parameter_star((star, name,)):
    return [{
        "type": "list_argument",
        "first_space": star.after_space,
        "name": name.value,
    }]

@pg.production("parameter : DOUBLE_STAR NAME")
def parameter_star_star((double_star, name,)):
    return [{
        "type": "dict_argument",
        "first_space": double_star.after_space,
        "second_space": double_star.after_space,
        "name": name.value,
    }]

@pg.production("argument : comma")
@pg.production("parameter : comma")
def parameter_comma((comma,)):
    return [comma]

@pg.production("suite : simple_stmt")
def suite((simple_stmt,)):
    return simple_stmt


@pg.production("suite : endls INDENT statements DEDENT")
def suite_indent((endls, indent, statements, dedent,)):
    return endls + statements


@pg.production("endls : endls endl")
@pg.production("endls : endl")
def endls(p):
    if len(p) == 1:
        return p[0]
    return p[0] + p[1]


include_imports(pg)
include_control_structures(pg)
include_primivites(pg)
include_operators(pg)
include_data_structures(pg)

@pg.production("atom : LEFT_PARENTHESIS yield_expr RIGHT_PARENTHESIS")
def yield_atom((left_parenthesis, yield_expr, right_parenthesis)):
    return {
        "type": "yield_atom",
        "value": yield_expr["value"],
        "first_space": left_parenthesis.after_space,
        "second_space": right_parenthesis.before_space,
        "third_space": yield_expr["space"]
    }

@pg.production("atom : BACKQUOTE testlist1 BACKQUOTE")
def repr_atom((backquote, testlist1, backquote2)):
    return {
        "type": "repr",
        "value": testlist1,
        "first_space": backquote.after_space,
        "second_space": backquote2.before_space,
    }

@pg.production("testlist1 : test comma testlist1")
def testlist1_double((test, comma, test2,)):
    return [test, comma] + test2

@pg.production("testlist1 : test")
def testlist1((test,)):
    return [test]

@pg.production("atom : INT")
def int((int_,)):
    return create_node_from_token(int_, section="number")


@pg.production("atom : name")
def atom_name((name,)):
    return name


@pg.production("atom : STRING")
def string((string_,)):
    return create_node_from_token(string_)


@pg.production("comma : COMMA")
def comma((comma,)):
    return {
        "type": "comma",
        "first_space": comma.before_space,
        "second_space": comma.after_space,
    }

parser = pg.build()


def fake_lexer(sequence):
    for i in tokenize(sequence):
        if i is None:
            yield None
        yield Token(*i)


def parse(sequence):
    return parser.parse(fake_lexer(sequence))
