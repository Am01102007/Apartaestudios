"""Propietarios y apartaestudios (módulo 2).

Es un solo dominio porque sus reglas se cruzan: un apartaestudio exige un propietario activo
y un propietario no se desactiva con apartaestudios activos. Separarlos crearía una
dependencia circular entre dos servicios.
"""
