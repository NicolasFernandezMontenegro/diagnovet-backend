import re
from typing import Optional, List
from app.schemas.domain import Report, Patient, Owner, Veterinarian

class ReportParser:
    def __init__(self, text: str):
        self.text = text

    def _clean_value(self, value: str) -> Optional[str]:
        if not value:
            return None
        cleaned = re.sub(r'\s+', ' ', value).strip()
        cleaned = cleaned.strip(".:-_,")
        if len(cleaned) > 100:
            return None
        return cleaned or None

    def _extract_field(self, keys: List[str], stop_words: List[str] = []) -> Optional[str]:
        keys_pattern = "|".join(keys)
        pattern = rf"(?i)(?:^|\n)\s*(?:{keys_pattern})\s*[:.-]?\s*(.*?)(?=\n|$)"
        
        match = re.search(pattern, self.text)
        if match:
            raw_value = match.group(1)
            for stop in stop_words:
                stop_pattern = rf"(?i)\s*{stop}[:.]?"
                split_match = re.split(stop_pattern, raw_value)
                if len(split_match) > 1:
                    raw_value = split_match[0]
                    break
            return self._clean_value(raw_value)
        return None

    def parse(self) -> Report:
        common_stops = ["Sexo", "Edad", "Raza", "Especie", "Propietario", "Fecha", "Profesional", "Veterinario"]

        patient = Patient(
            name=self._extract_field(["Paciente", "Nombre", "Nombre del Paciente"], stop_words=["Propietario", "Especie", "Raza"]),
            species=self._extract_field(["Especie", "Esp"], stop_words=common_stops),
            breed=self._extract_field(["Raza"], stop_words=["Sexo", "Genero", "Color", "Edad"]),
            sex=self._extract_field(["Sexo", "Genero"], stop_words=["Edad", "Castrado", "Fecha"]),
            age=self._extract_field(["Edad", "Años"], stop_words=["Fecha", "Peso", "Sexo", "DATOS"]),
        )

        owner = Owner(
            name=self._extract_field(["Propietario", "Dueño", "Tutor"], stop_words=["Tel", "Dirección", "Especie", "Edad"]),
            contact=self._extract_field(["Teléfono", "Celular", "Tel", "Email", "Contacto"], stop_words=[]),
        )

        veterinarian = Veterinarian(
            name=self._extract_field(
                ["Veterinario responsable", "Veterinario", "Vet", "Dr.", "Dra.", "Profesional", "Referido por", "Solicitante"], 
                stop_words=["Matrícula", "Clínica", "Dirección", "Fecha", "M.P."]
            ),
            clinic=self._extract_field(["Clínica Veterinaria", "Clínica", "Centro", "Hospital"], stop_words=["Referido", "Dirección", "Tel"]),
        )

        
        findings = self._extract_block(
            start_keys=[
                "ESTUDIO RADIOLOGICO", "HALLAZGOS ECOGRÁFICOS", "DESCRIPCIÓN", 
                "HALLAZGO BIDIMENSIONAL", "Ojo izquierdo", "INFORME ECOGRÁFICO"
            ],
            end_keys=["DIAGNOSTICO", "CONCLUSION", "COMENTARIOS", "RECOMENDACIONES", "Dr.", "M.V."],
            ignore_lines=["Veterinario", "Técnica", "Profesional", "Fecha", "Paciente", "Propietario", "DATOS", "Solicitado", "Clínica"]
        )
        
        conclusion = self._extract_block(
            start_keys=["DIAGNOSTICO", "CONCLUSION", "IMPRESIÓN DIAGNÓSTICA", "COMENTARIOS"],
            end_keys=["RECOMENDACIONES", "SUGERENCIAS", "TRATAMIENTO", "Dr.", "M.V.", "Mat."],
            ignore_lines=["Dr.", "M.V."]
        )

        full_diagnosis_parts = []
        if findings: full_diagnosis_parts.append(findings)
        if conclusion: full_diagnosis_parts.append(f"\nCONCLUSIÓN:\n{conclusion}")
        
        full_diagnosis = "\n\n".join(full_diagnosis_parts) if full_diagnosis_parts else None

        recommendations = self._extract_block(
            start_keys=["RECOMENDACIONES", "SUGERENCIAS", "TRATAMIENTO", "INDICACIONES"],
            end_keys=["Dr.", "M.V.", "Saluda", "Firma"],
            ignore_lines=[]
        )

        return Report(
            patient=patient,
            owner=owner,
            veterinarian=veterinarian,
            diagnosis=full_diagnosis,
            recommendations=recommendations
        )

    def _extract_block(self, start_keys: List[str], end_keys: List[str], ignore_lines: List[str]) -> Optional[str]:
        lines = self.text.splitlines()
        collecting = False
        buffer = []
        
        start_pattern = "|".join(start_keys)
        end_pattern = "|".join(end_keys)
        ignore_pattern = "|".join(ignore_lines) if ignore_lines else None
        
        for line in lines:
            clean_line = line.strip()
            if not clean_line:
                continue

            if not collecting:
                if re.search(rf"(?i)(?:^|\n)\s*({start_pattern})", line):
                    collecting = True
                    content_after_title = re.sub(rf"(?i)^\s*({start_pattern})[:.-]*\s*", "", line)
                    if content_after_title.strip():
                        buffer.append(content_after_title.strip())
                    continue
            
            if collecting:
                if re.match(rf"(?i)^\s*({end_pattern})[:.]?", clean_line):
                    break
                
                if re.match(r"(?i)^\s*(Dr\.|Lic\.|M\.V\.|Mat\.|M\.P\.)", clean_line):
                    break

                if ignore_pattern and re.match(rf"(?i)^\s*({ignore_pattern})", clean_line):
                    continue
                
                buffer.append(clean_line)

        return "\n".join(buffer).strip() or None