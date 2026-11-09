"""Les vecteurs de phrases de l'hybride (TP5.2, phase 4) : all-MiniLM-L6-v2, ou un encodeur factice.

Le modèle de catégorie assemble les TF-IDF (mots, caractères) et ces vecteurs (src/train.py) ; la recherche
d'articles fait de même (src/kb.py). Mesuré sur la validation, 3 graines : F1 macro 0,791 -> 0,847, top-3 des
articles 85,7 % -> 96,2 % (docs/semaine5.2.md, python src/essai_minilm.py).

Le mode est choisi à l'entraînement et gardé dans le modèle (paramètre « mode ») : un modèle entraîné avec
MiniLM sert MiniLM, un modèle entraîné avec l'encodeur factice sert l'encodeur factice.
  SUPPORT_ENCODEUR=minilm   (par défaut) le vrai encodeur, téléchargé une fois dans le cache Hugging Face
  SUPPORT_ENCODEUR=factice  des vecteurs de n-grammes hachés, de même dimension, sans téléchargement : la CI
  python src/train.py --sans-minilm   le modèle sans vecteurs de phrases (le repli, celui de la phase 3 bis)
"""
import os
from collections import OrderedDict

import numpy as np
from scipy.sparse import csr_matrix
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import HashingVectorizer
from sklearn.preprocessing import normalize

NOM_MINILM = "sentence-transformers/all-MiniLM-L6-v2"
DIMENSION = 384
MODES = {"minilm", "factice"}
TAILLE_CACHE = 5000


def mode_demande() -> str:
    """Le mode demandé pour un nouvel entraînement (variable SUPPORT_ENCODEUR)."""
    mode = os.environ.get("SUPPORT_ENCODEUR", "minilm").strip().lower()
    if mode not in MODES:
        raise ValueError(f"SUPPORT_ENCODEUR={mode!r} : valeurs possibles {sorted(MODES)}")
    return mode


class EncodeurIndisponible(RuntimeError):
    """sentence-transformers ou le modèle all-MiniLM-L6-v2 manque : l'API refuse de démarrer."""


class Phrases(BaseEstimator, TransformerMixin):
    """Un texte -> un vecteur normalisé de dimension 384, multiplié par poids, en matrice creuse
    (pour s'assembler aux TF-IDF dans un FeatureUnion). Un cache borné évite de réencoder le même texte
    (le classement et la recherche d'articles lisent le même message)."""

    _modeles: dict[str, object] = {}
    _cache: "OrderedDict[tuple[str, str], np.ndarray]" = OrderedDict()

    def __init__(self, poids: float = 1.0, mode: str | None = None):
        self.poids = poids
        self.mode = mode

    def fit(self, textes, y=None):
        if self.mode is None:
            self.mode = mode_demande()
        return self

    @classmethod
    def _minilm(cls):
        if "minilm" not in cls._modeles:
            try:
                from sentence_transformers import SentenceTransformer

                cls._modeles["minilm"] = SentenceTransformer(NOM_MINILM)
            except Exception as erreur:  # paquet absent, pas de réseau ni de cache
                raise EncodeurIndisponible(
                    f"encodeur {NOM_MINILM} indisponible ({type(erreur).__name__}) : installez sentence-transformers "
                    "et téléchargez le modèle une fois, ou entraînez sans lui (python src/train.py --sans-minilm)"
                ) from None
        return cls._modeles["minilm"]

    def _encoder(self, textes: list[str]) -> np.ndarray:
        if (self.mode or "minilm") == "factice":
            hache = HashingVectorizer(analyzer="char_wb", ngram_range=(3, 4), n_features=DIMENSION, alternate_sign=True)
            return normalize(hache.transform(textes)).toarray().astype(np.float32)
        return np.asarray(self._minilm().encode(textes, batch_size=64, normalize_embeddings=True,
                                                show_progress_bar=False), dtype=np.float32)

    def transform(self, textes):
        textes = [str(t) for t in textes]
        mode = self.mode or "minilm"
        connus = {t: self._cache[(mode, t)] for t in dict.fromkeys(textes) if (mode, t) in self._cache}
        nouveaux = [t for t in dict.fromkeys(textes) if t not in connus]
        if nouveaux:
            connus.update(zip(nouveaux, self._encoder(nouveaux), strict=True))
        resultat = csr_matrix(np.vstack([connus[t] for t in textes]) * self.poids)
        for texte in nouveaux:  # le cache garde les derniers textes encodés, TAILLE_CACHE au plus
            self._cache[(mode, texte)] = connus[texte]
        while len(self._cache) > TAILLE_CACHE:
            self._cache.popitem(last=False)
        return resultat


def mode_du_modele(pipeline) -> str | None:
    """Le mode de l'encodeur d'un modèle de catégorie, ou None s'il n'a pas de vecteurs de phrases."""
    etape = getattr(pipeline, "named_steps", {}).get("tfidf")
    for nom, partie in getattr(etape, "transformer_list", []):
        if nom == "phrases":
            return partie.mode or "minilm"
    return None
