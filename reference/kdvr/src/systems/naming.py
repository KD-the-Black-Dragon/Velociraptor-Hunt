from __future__ import annotations

from tcod.ecs import Entity

from src.components import DisplayName, ProperName, SpeciesId

DEFAULT_SPECIES = "creature"


def entity_species(entity: Entity) -> str:
    """Species/type string without article."""
    display = entity.components.get(DisplayName)
    return display.name if display is not None else DEFAULT_SPECIES


def entity_type_id(entity: Entity) -> str:
    """Entity definition id from data (falls back to display species name)."""
    species_id = entity.components.get(SpeciesId)
    if species_id is not None:
        return species_id.id
    return entity_species(entity)


def _article_label(entity: Entity) -> str:
    """Mid-sentence label with article when needed: 'Fang' or 'the wolf'."""
    proper = entity.components.get(ProperName)
    if proper is not None:
        return proper.name
    return f"the {entity_species(entity)}"


def _indefinite_article(word: str) -> str:
    """Simple a/an for species names (first letter only)."""
    if not word:
        return "a"
    return "an" if word[0].lower() in "aeiou" else "a"


def _indefinite_label(entity: Entity) -> str:
    """Mid-sentence label: 'Fang' or 'a wolf' / 'an owl mage'."""
    proper = entity.components.get(ProperName)
    if proper is not None:
        return proper.name
    species = entity_species(entity)
    return f"{_indefinite_article(species)} {species}"


def entity_log_name(entity: Entity, *, sentence_start: bool = False) -> str:
    """Name for log messages: ProperName verbatim, else 'the {species}'."""
    label = _article_label(entity)
    if sentence_start:
        return label[0].upper() + label[1:]
    return label


def entity_log_name_indefinite(entity: Entity, *, sentence_start: bool = False) -> str:
    """Name for log messages: ProperName, else 'a/an {species}'."""
    label = _indefinite_label(entity)
    if sentence_start:
        return label[0].upper() + label[1:]
    return label


def entity_log_possessive(entity: Entity, *, sentence_start: bool = False) -> str:
    """Possessive for log messages: \"Fang's\" or \"the wolf's\"."""
    label = f"{_article_label(entity)}'s"
    if sentence_start:
        return label[0].upper() + label[1:]
    return label


def entity_display_name(entity: Entity) -> str:
    """Short label for narratives (proper name or species, no article)."""
    proper = entity.components.get(ProperName)
    if proper is not None:
        return proper.name
    return entity_species(entity)