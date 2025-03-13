from typing import List, Dict, Set, Optional, Union
from instantneo.skills.skill_manager import SkillManager

class SkillManagerOperations:
    @staticmethod
    def union(*managers: "SkillManager") -> "SkillManager":
        """
        Devuelve un SkillManager que contiene la unión de todos
        los skills registrados en los managers pasados.
        """
        unified_manager = SkillManager()
        for m in managers:
            for func in m.registry.values():
                unified_manager.register_skill(func)
        return unified_manager

    @staticmethod
    def intersection(*managers: "SkillManager") -> "SkillManager":
        """
        Devuelve un SkillManager con los skills que aparecen en
        TODOS los managers pasados. Se basa en el nombre de la función.
        """
        if not managers:
            # Si no se pasa ningún manager, retornamos uno vacío
            return SkillManager()

        # 1. Obtenemos la intersección de nombres
        common_names = set(managers[0].get_skill_names())
        for m in managers[1:]:
            common_names &= set(m.get_skill_names())

        # 2. Creamos un nuevo manager con los skills de common_names
        intersection_manager = SkillManager()
        
        # Tomamos las funciones del PRIMER manager, asumiendo que 
        # son idénticas en los demás. (Si quisieras verificar si 
        # son realmente la misma función o metadata, podrías añadir lógica.)
        for name in common_names:
            func = managers[0].get_skill_by_name(name)
            # get_skill_by_name podría devolver dict si hay duplicados, 
            # aquí simplificamos asumiendo que hay solo una función.
            if callable(func):
                intersection_manager.register_skill(func)
        
        return intersection_manager

    @staticmethod
    def difference(base_manager: "SkillManager", exclude_manager: "SkillManager") -> "SkillManager":
        """
        Devuelve un nuevo SkillManager con los skills que están
        en base_manager pero NO en exclude_manager.
        """
        base_names = set(base_manager.get_skill_names())
        exclude_names = set(exclude_manager.get_skill_names())

        diff_names = base_names - exclude_names

        diff_manager = SkillManager()
        for name in diff_names:
            func = base_manager.get_skill_by_name(name)
            if callable(func):
                diff_manager.register_skill(func)
        return diff_manager

    @staticmethod
    def symmetric_difference(manager_a: "SkillManager", manager_b: "SkillManager") -> "SkillManager":
        """
        Devuelve un SkillManager con la 'diferencia simétrica' de
        los skills de manager_a y manager_b. Es decir, skills que
        están en A o en B, pero NO en ambos.
        """
        a_names = set(manager_a.get_skill_names())
        b_names = set(manager_b.get_skill_names())

        # ^ es el operador de diferencia simétrica en Python
        sym_diff_names = a_names ^ b_names

        sym_diff_manager = SkillManager()
        for name in sym_diff_names:
            # Verificamos si el skill está en A o en B (o en ambos, pero con duplicados)
            func_a = manager_a.get_skill_by_name(name)
            func_b = manager_b.get_skill_by_name(name)

            # Si está en A y no en B, lo tomamos de A
            if func_a and not func_b:
                if callable(func_a):
                    sym_diff_manager.register_skill(func_a)
            # Si está en B y no en A, lo tomamos de B
            elif func_b and not func_a:
                if callable(func_b):
                    sym_diff_manager.register_skill(func_b)
            # Si existe en ambos (en teoría no debería ocurrir en una dif. simétrica),
            # podrías decidir cómo manejarlo, pero en teoría no entra aquí.

        return sym_diff_manager

    @staticmethod
    def compare(manager_a: "SkillManager", manager_b: "SkillManager") -> Dict[str, Set[str]]:
        """
        Retorna un diccionario con:
          - 'common_skills': nombres de skills presentes en ambos managers
          - 'unique_to_a': nombres de skills presentes solo en manager_a
          - 'unique_to_b': nombres de skills presentes solo en manager_b
        """
        a_names = set(manager_a.get_skill_names())
        b_names = set(manager_b.get_skill_names())

        return {
            "common_skills": a_names & b_names,
            "unique_to_a": a_names - b_names,
            "unique_to_b": b_names - a_names
        }