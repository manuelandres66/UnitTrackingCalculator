from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
import json
from sympy.parsing.sympy_parser import parse_expr
from sympy.physics.units.util import quantity_simplify
from sympy.physics.units import ( convert_to,
    meter, centimeter, foot, second, kilogram, gram, newton, joule, pascal, psi, watt, foot, s
)
from sympy.physics.units.systems.si import SI
from sympy import simplify, Symbol, Mul,Pow, preorder_traversal


# Create your views here.
# Define CGS base units
dyne = gram * centimeter / second**2
ba = gram / (centimeter * second**2)
erg = gram * centimeter**2 / second**2
erg_per_s = erg / second
slug = 14.5939 * kilogram

DYNE = Symbol("dyne")
ERG = Symbol("erg")
BA = Symbol("Ba")
ERG_S = Symbol("erg_s")
SLUG = Symbol("slug")

pound = 0.45359237 * kilogram
g = 9.80665 * meter / second**2
lbf = 4.44822 * newton
ft_lb = foot * lbf        # foot‐pound (energy)
ft_lb_s = ft_lb / second   # foot‐pound per second (power)

LBF = Symbol("lbf")
FT_LB = Symbol("ftlb")
FT_LB_S = Symbol("ftlb_s")
PSI = Symbol("PSI")

local_units = {
    "m/s**2": meter / second**2,
    "cm/s**2": centimeter / second**2,
    "ft/s**2": foot / second**2,
    "m**2" : meter**2,
    "cm": centimeter,
    "ft": foot,
    "kg": kilogram,
    "g": gram,
    "slug": slug,
    "cm/s": centimeter / second,
    "ft/s": foot / second,
    "N": newton,
    "m/s": meter / second,
    "dyne": dyne,
    "lbf": lbf,
    "erg": erg,
    "m": meter,
    "ftlb": ft_lb,
    "Pa": pascal,
    "Ba": 0.1 * pascal,
    "PSI": psi,
    "W": watt,
    "J": joule,
    "erg_s": erg / second,
    "ftlb_s": ft_lb_s,
    's' : second,
    "J^2" : joule**2,
    'cm^2' : centimeter**2,
    'cm*erg/s' : centimeter*erg_per_s,
    'cm*erg': centimeter*erg,
    'ft^2': foot**2,
    'ftlb': foot*newton,
}

imp_units = {
    'ft^2': [1, foot**2],
    "ft/s": [1, foot / second],
    "ft/s**2": [1, foot / second**2],
    'ft' : [1, foot],
    'ftlb': [1/4.4482216152605 , foot*newton],
    'slug*ft' : [0.22481, kilogram*meter],
    'ft*ftlb' : [2.4183999, joule*meter],
    'ft*PSI' : [6894.76, newton/foot]
}

local_units = dict(sorted(local_units.items(), key=lambda item: len(str(item[1])), reverse=True))
imp_units = dict(sorted(imp_units.items(), key=lambda item: len(str(item[1])), reverse=True))

def index(request):
    return render(request, "calc/index.html")

def clean_str(x):
    if isinstance(x, float) and x.is_integer():
        return str(int(x))
    return str(x)



def to_si(expr):
    if expr.has(erg_per_s) or expr.has(ft_lb_s) or expr.has(watt) or expr.has(foot*newton/second):
        expr.replace(centimeter**2 * gram / second**3, erg_per_s)
        to_simplify = simplify(convert_to(expr, watt))
    elif expr.has(erg) or expr.has(foot*newton):
        to_simplify = simplify(convert_to(expr, joule))
    elif expr.has(ba) or expr.has(psi) or expr.has(pascal) or expr.has(newton/foot**2):
        to_simplify = simplify(convert_to(expr, pascal))
    elif expr.has(dyne) or expr.has(lbf):
        to_simplify = simplify(convert_to(expr, newton))
    elif expr.has(newton):
        to_simplify = simplify(expr)
    else:
        to_simplify = simplify(convert_to(expr, [meter, kilogram, second]))
  
    return quantity_simplify(to_simplify)

def to_cgs(expr):
    from sympy.physics.units import centimeter
    if expr.has(watt) or expr.has(foot*newton/second):
        to_simplify = simplify(convert_to(expr, erg_per_s) / erg_per_s) * ERG_S
    elif expr.has(joule) or expr.has(foot * newton):
        expr.replace(foot * newton, ft_lb)
        to_simplify = simplify(convert_to(expr, erg) / erg) * ERG
    elif expr.has(pascal) or expr.has(psi):
        to_simplify = simplify(convert_to(expr, ba) / ba) * BA
    elif expr.has(newton) or expr.has(lbf):
        to_simplify = simplify(convert_to(expr, dyne) / dyne) * DYNE
    else:
        to_simplify = simplify(convert_to(expr, [centimeter, gram, second]))

    return quantity_simplify(to_simplify)
    

def to_imperial(expr):
    if expr.has(joule) or expr.has(erg):
        to_simplify = simplify(convert_to(expr, ft_lb) / ft_lb) * FT_LB
    elif expr.has(watt) or expr.has(erg_per_s):
        to_simplify = simplify(convert_to(expr, ft_lb_s) / ft_lb_s) * FT_LB_S
    elif expr.has(pascal) or expr.has(ba):
        to_simplify = simplify(convert_to(expr, psi))
    elif expr.has(newton) or expr.has(dyne):
        to_simplify = simplify(convert_to(expr, lbf) / lbf) * LBF
    elif expr.has(kilogram) or expr.has(gram):
        to_simplify = simplify(convert_to(expr, slug) / slug) * SLUG
    else:
        to_simplify = simplify(convert_to(expr, [foot, pound, second]))
    return quantity_simplify(to_simplify)


def sympy_unit(unit_str):
    unit_str = unit_str.strip().replace("^", "**")
    expr = parse_expr(unit_str, local_dict=local_units, evaluate=True)
    return expr

def format_raw_units(expr, precision=6):
    unit_symbol_map =  {str(v): k for k, v in local_units.items()}
    if isinstance(expr, Mul):
        coeff = 1
        numerators = []
        denominators = []

        for arg in expr.args:
            if arg.is_number:
                coeff *= float(arg)
            elif isinstance(arg, Pow) and arg.exp.is_Number and arg.exp < 0:
                base = arg.base
                exp = -arg.exp
                base_str = unit_symbol_map.get(str(base), str(base))
                denominators.append(f"{base_str}^{int(exp)}" if exp != 1 else base_str)
            else:
                unit_str = unit_symbol_map.get(str(arg), str(arg))
                numerators.append(unit_str)

        num_str = "*".join(numerators)
        denom_str = "*".join(denominators)

        if denom_str:
            unit_str = f"{num_str}/{denom_str}" if num_str else f"1/{denom_str}"
        else:
            unit_str = num_str

        value_to_str = clean_str(round(coeff, precision))
        return f"{value_to_str} {unit_str}".strip().replace('**', '^')

    elif expr.is_number:
        return clean_str(round(float(expr), precision))
    else:
        return clean_str(expr).replace('**', '^')
    
def format_with_named_units(expr, precision=6, imperial=False):
    print("\n EXPRRESION TO FORMAT:", expr)
    if not imperial:
        for symbol, unit in local_units.items():
            try:
                if expr.has(unit):
                    value = float(expr / unit)
                    if round(value, precision) == 0:
                        return '0'
                    value_to_str = clean_str(round(value, precision))
                    return f"{value_to_str} {symbol}".replace('**', '^')
            except Exception:
                continue
        return format_raw_units(expr, precision)
    else:
        for symbol, unit_with_conversion in imp_units.items():
            try:
                if expr.has(unit_with_conversion[1]):
                    print("FACTOR", float(expr / unit_with_conversion[1]), unit_with_conversion[0])
                    value = float(expr / unit_with_conversion[1]) * unit_with_conversion[0]
                    print(value)
                    if round(value, precision) == 0:
                        return '0'
                    value_to_str = clean_str(round(value, precision))
                    print(unit_with_conversion, symbol)
                    return f"{value_to_str} {symbol}".replace('**', '^')
            except Exception:
                continue
        return format_raw_units(expr, precision)

def value_sum_rest(expr, system):
    if system == "MKS":
        return format_with_named_units(to_si(expr))
    elif system == "CGS":
        return format_with_named_units(to_cgs(expr))
    elif system == "IMP":
        return format_with_named_units(to_imperial(expr))

def reduced(expr, type_units, imperial=False):
    print("EXPRESSION:", expr)
    best = expr
    _, unit_expr = expr.as_coeff_Mul()
    best_lenght = 200
    for unit in type_units:
        converted = convert_to(expr, unit)
        _, unit_conv = converted.as_coeff_Mul()
        converted_lenght = len(str(unit_conv))
        unit_conv_list = list({x for x in preorder_traversal(converted) if hasattr(x, 'dimension')})
        is_in_system = set(unit_conv_list).issubset(set(type_units))
        print("1_", converted, "lenght", converted_lenght, "best", best_lenght, 'insystem', is_in_system, "list", unit_conv_list)
        if is_in_system and converted_lenght < best_lenght:
            best_lenght = converted_lenght
            best = converted
    if best == expr and imperial:
        best = to_si(expr)
    print(best)
    return best

def value_mul_div(expr, system):
    if system == "MKS":
        si_units = [meter, second, kilogram, newton, pascal, 
                    meter/second, meter/second**2, joule, watt, 
                    newton/meter, meter**2, joule*meter, pascal*meter, 
                    watt*meter]
        si_units = sorted(si_units, key=lambda u: len(str(u)), reverse=True)
        return format_with_named_units(reduced(expr, si_units))
    elif system == "CGS":
        cgs_units = [centimeter, second, gram, dyne, ba, 
                     centimeter / second, centimeter / second**2, erg, erg / second, 
                     dyne / centimeter, centimeter**2, erg*centimeter,
                     gram*centimeter, centimeter*erg_per_s]
        cgs_units = sorted(cgs_units, key=lambda u: len(str(u)), reverse=True)
        return format_with_named_units(reduced(expr, cgs_units))
    elif system == "IMP":
        imperial_units = [ foot, second, pound, lbf, psi, foot / second, 
                          foot / second**2, foot * lbf, foot * lbf / second, 
                          lbf / foot, foot**2, slug*foot, foot*pound, foot*newton, newton]
        imperial_units = sorted(imperial_units, key=lambda u: len(str(u)), reverse=True)
        return format_with_named_units(reduced(expr, imperial_units, imperial=True), imperial=True)

def operation(request):
    if request.method == "POST":
        data = json.loads(request.body)
        operant = data["operant"]
        first_value, first_unit = data['firstPart'][0],  data['firstPart'][1]
        second_value, second_unit = data['secondPart'][0],  data['secondPart'][1]
        system = data['system']
        result = None
        error = False

        first = sympy_unit(first_unit) * float(first_value)
        second = sympy_unit(second_unit) * float(second_value)
        print('\n \n')
        if operant == '+':
            result = value_sum_rest(first + second, system)
        elif operant == '-':
            result = value_sum_rest(first - second, system)
        elif operant == 'x':
            result = value_mul_div(first * second, system)
        elif operant == '/':
            result = value_mul_div(first / second, system)

        if len(result.split(" ")) == 1:
            result = result + ' (1)'

        if "+" in result or " - " in result:
            error = "Impossible Operation"

    return JsonResponse({'result': result, 'error': error})