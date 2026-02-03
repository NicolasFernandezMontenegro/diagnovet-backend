

from typing import Optional
from app.schemas.domain import Report, Patient, Owner, Veterinarian


class ReportParser:
    def __init__(self, text: str):
        self.text = text

    def _extract_field(self, label: str) -> Optional[str]:
        """
        Busca líneas tipo:
        Nombre: Chester
        Especie: Canino
        """
        for line in self.text.splitlines():
            if label.lower() in line.lower():
                if ":" in line:
                    return line.split(":", 1)[1].strip() or None
        return None

    def parse(self) -> Report:
        patient = Patient(
            name=self._extract_field("Nombre"),
            species=self._extract_field("Especie"),
            breed=self._extract_field("Raza"),
            sex=self._extract_field("Sexo"),
            age=self._extract_field("Edad"),
        )

        owner = Owner(
            name=self._extract_field("Propietario"),
            contact=None,
        )

        veterinarian = Veterinarian(
            name=self._extract_field("Veterinario"),
            clinic=self._extract_field("Clínica"),
        )

        diagnosis = self._extract_section("ESTUDIO RADIOLOGICO")

        return Report(
            patient=patient,
            owner=owner,
            veterinarian=veterinarian,
            diagnosis=diagnosis,
        )

    def _extract_section(self, header: str) -> Optional[str]:
        """
        Extrae texto a partir de un encabezado hasta el siguiente bloque grande
        """
        lines = self.text.splitlines()
        collecting = False
        buffer = []

        for line in lines:
            if header.lower() in line.lower():
                collecting = True
                continue

            if collecting:
                if line.strip().isupper() and len(line.strip()) > 5:
                    break
                buffer.append(line)

        result = "\n".join(buffer).strip()
        return result or None
