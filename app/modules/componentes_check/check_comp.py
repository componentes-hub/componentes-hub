import re

VALID_COMPONENT_TYPES = {
    "processor",
    "graphics",
    "memory",
    "storage",
    "power_supply",
    "cooling",
    "case",
    "network",
    "capture_card",
    "sound_card",
    "antenna",
    "dvd_drive",
    "encoder"
}

class PCCompFileChecker:

    def __init__(self, text_content: str):
        self.raw_text = text_content

        # Diccionario donde guardamos los datos ya procesados
        self.parsed_data = {
            "name": None,
            "version": None,
            "author": None,
            "properties": {}
        }

        self.errors = []

        self._parse()
        self._validate()

    # Parseo del archivo .comp
    def _parse(self):
        """Lee el archivo .comp y extrae sus campos y propiedades."""

        lines = self.raw_text.strip().splitlines()
        if not lines:
            self.errors.append("El archivo está vacío.")
            return

        # Parseo de cabecera: name, version, author
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue

            match = re.match(r"^([a-zA-Z0-9_]+)\s*:\s*(.*)$", stripped)
            if match:
                key = match.group(1).lower()
                value = match.group(2).strip()

                if key in ("name", "version", "author"):
                    self.parsed_data[key] = value

                if key == "properties":
                    break  # el resto corresponde a propiedades

        # Parseo del bloque de propiedades
        try:
            start_index = next(
                i for i, l in enumerate(lines) if l.strip().lower().startswith("properties:")
            )
        except StopIteration:
            self.errors.append("No se encontró la sección 'properties:'.")
            return

        property_lines = lines[start_index + 1:]

        for line in property_lines:
            stripped = line.strip()
            if not stripped:
                continue

            # Formato esperado: key: value
            match = re.match(r"^([a-zA-Z0-9_]+)\s*:\s*(.*)$", stripped)
            if match:
                key = match.group(1).lower()
                value = match.group(2).strip()
                self.parsed_data["properties"][key] = value
            else:
                self.errors.append(f"Propiedad mal formada: '{stripped}'")

    # Validaciones del contenido
    def _validate(self):
        """Valida que el archivo cumpla con los requisitos del formato."""

        # Validar campos obligatorios del archivo
        for required_field in ("name", "version", "author"):
            if not self.parsed_data[required_field]:
                self.errors.append(f"Falta el campo obligatorio: '{required_field}'")

        properties = self.parsed_data["properties"]

        if not properties:
            self.errors.append("La sección 'properties' está vacía.")
            return

        # Validación de campos obligatorios dentro de properties
        required_properties = ("id", "type", "model", "description")

        for prop in required_properties:
            if prop not in properties:
                self.errors.append(f"Falta la propiedad obligatoria: '{prop}'")

        # Si falta "type", no seguimos validando el tipo
        if "type" not in properties:
            return

        comp_type = properties["type"].lower()

        # Tipo válido
        if comp_type not in VALID_COMPONENT_TYPES:
            self.errors.append(f"Tipo de componente no válido: '{comp_type}'")

        # Validaciones específicas por tipo
        model_value = properties.get("model", "").lower()

        if comp_type == "processor":
            if not any(brand in model_value for brand in ("intel", "amd")):
                self.errors.append(
                    f"Processor inválido o marca desconocida en model: '{properties.get('model')}'"
                )

        if comp_type == "graphics":
            if not any(brand in model_value for brand in ("nvidia", "amd", "intel")):
                self.errors.append(
                    f"Graphics inválido o marca desconocida en model: '{properties.get('model')}'"
                )

        if comp_type == "storage":
            if not any(keyword in model_value for keyword in ("ssd", "hdd", "nvme")):
                self.errors.append(
                    f"Tipo de almacenamiento desconocido en model: '{properties.get('model')}'"
                )

    # Métodos públicos
    def is_valid(self) -> bool:
        """Indica si el archivo .comp es válido."""
        return len(self.errors) == 0

    def get_parsed_data(self) -> dict:
        """Devuelve los datos procesados del archivo."""
        return self.parsed_data

    def get_errors(self) -> list:
        """Devuelve la lista de errores encontrados."""
        return self.errors
