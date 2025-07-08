from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
import json
import re
from pint import UnitRegistry

ur = UnitRegistry()
Q_ = ur.Quantity

substitutions = {
    '[mass]': {
        'SI': 'kilogram',
        'CGS': 'gram',
        'IMP': 'slug',
    },
    '[length]': {
        'SI': 'meter',
        'CGS': 'centimeter',
        'IMP': 'foot',
    },
    '[time]': {
        'SI': 'second',
        'CGS': 'second',
        'IMP': 'second',
    }
}

SI_UNITS = [
    ur.meter, ur.second, ur.kilogram, ur.newton,
    ur.pascal, ur.joule, ur.watt, ur.hertz, 
    ur.meter/ur.second, ur.meter/ur.second**2,
    ur.joule*ur.meter, ur.watt*ur.meter
]

CGS_UNITS = [
    ur.centimeter, ur.second, ur.gram, ur.dyne,
    ur.barye, ur.erg, ur.stokes, 
    ur.centimeter/ur.second, ur.centimeter/ur.second**2,
    ur.erg/ur.second, ur.centimeter**2, ur.centimeter*ur.gram,
    ur.centimeter**2/ur.second**2, ur.centimeter*ur.erg,
    ur.gram/ur.second**2, ur.cm*ur.erg/ur.s, ur.cm*ur.s
]

IMP_UNITS = [
    ur.foot, ur.second, ur.slug, ur.pound_force,
    ur.psi, ur.foot**2 / ur.second,
    ur.foot / ur.second, ur.foot / ur.second**2, ur.foot**2, ur.slug * ur.foot,
    ur.foot**2 / ur.second**2, ur.foot * ur.foot * ur.pound_force, 
    ur.foot * ur.foot * ur.pound_force / ur.second,
    ur.foot * ur.second, ur.horsepower, ur.foot*ur.lbf, ur.foot*ur.psi
]

SYSTEMS = {
    "MKS": SI_UNITS,
    "CGS": CGS_UNITS,
    "IMP": IMP_UNITS,
}



def index(request):
    return render(request, "calc/index.html")

def format_number(value, digits=6):
    rounded = round(value, digits)
    if rounded == int(rounded):
        return str(int(rounded))
    else:
        return f"{rounded:.{digits}f}".rstrip('0').rstrip('.')

def pint_unit(string_unit):
    return ur.parse_expression(string_unit).units

def value_expr(expr, system):
    base = expr.to_base_units()
    system_name = system
    dims = base.dimensionality
    new_unit_expr = ''
    for dim, power in dims.items():
        if dim in substitutions and system_name in substitutions[dim]:
            new_unit = substitutions[dim][system_name]
            new_unit_expr += f'{new_unit}**{power} * '
        else:
            new_unit_expr += f'{dim}**{power} * '

    new_unit_expr = new_unit_expr.rstrip(' *')
    try:
        base = base.to(ur.parse_expression(new_unit_expr).units)
    except:
        pass

    for target_unit in SYSTEMS[system]:
        try:
            converted = base.to(target_unit)
            if converted.dimensionality == base.dimensionality:
                base = converted
        except:
            continue
    return base  


def operation(request):
    if request.method == "POST":
        data = json.loads(request.body)
        operant = data["operant"]
        print("HOLA",data)
        first_value, first_unit = data['firstPart'][0],  data['firstPart'][1]
        second_value, second_unit = data['secondPart'][0],  data['secondPart'][1]
        system = data['system']
        print('\n \n')
        
        first = pint_unit(first_unit) * float(first_value)
        second = pint_unit(second_unit) * float(second_value)
        print(first, second, first_unit)
        if operant == '+':
            units = value_expr(first + second, system)
        elif operant == '-':
            units = value_expr(first - second, system)
        elif operant == 'x':
            units = value_expr(first * second, system)
        elif operant == '/':
            units = value_expr(first / second, system)

    
    result_units = f'{units.units:~}'.replace(" ", "")
    result = f"{format_number(units.magnitude)} " + result_units
    result = result.replace('**', '^')
    if format_number(units.magnitude) == '0':
        result = '0'
    print('RESULTTTT', result)
    error = ""
    return JsonResponse({'result': result, 'error': error})