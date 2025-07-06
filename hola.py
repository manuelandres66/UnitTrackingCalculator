from pint import UnitRegistry
ureg = UnitRegistry()

hola = 3 * ureg.meter * 3 * ureg.pascal
print(hola.to('foot*psi'))