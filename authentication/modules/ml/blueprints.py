from aquilia.blueprints import Blueprint
from aquilia.blueprints.facets import FloatFacet, IntFacet, ListFacet

class IrisInputBlueprint(Blueprint):
    """Input payload for Iris classification."""
    sepal_length = FloatFacet(min_value=0, help_text="Sepal length in cm")
    sepal_width = FloatFacet(min_value=0, help_text="Sepal width in cm")
    petal_length = FloatFacet(min_value=0, help_text="Petal length in cm")
    petal_width = FloatFacet(min_value=0, help_text="Petal width in cm")

class IrisOutputBlueprint(Blueprint):
    """Output payoff for Iris classification."""
    species = IntFacet(help_text="Predicted species index (0: setosa, 1: versicolor, 2: virginica)")
    probability = ListFacet(child=FloatFacet(), help_text="Probabilities for each class")
