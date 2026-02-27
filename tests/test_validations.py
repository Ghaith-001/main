"""
TESTS D'INTÉGRATION — tests/test_validations.py
Tests pytest pour valider l'ensemble du pipeline de la plateforme.

Run: pytest tests/test_validations.py -v
"""

import os
import sys
import json
import sqlite3
import tempfile
import shutil
import numpy as np
import pytest

# Ajouter le dossier parent au path
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

# Chemin DB de test (séparé de la DB principale)
TEST_DB = os.path.join(tempfile.gettempdir(), "test_plateforme.sqlite")
TEST_PARAMS = {
    "IS": 7.62767e-9,
    "RS": 0.0341512,
    "N":  1.80803,
    "BV": 1000,
    "IBV": 5e-8,
    "CJO": 1e-11,
    "VJ":  0.7,
    "M":   0.5,
    "FC":  0.5,
    "TT":  1e-7,
    "EG":  1.65743,
    "XTI": 5,
    "KF":  0,
    "AF":  1,
}


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def test_db_path(tmp_path_factory):
    """Crée une DB SQLite temporaire pour les tests."""
    db_dir = tmp_path_factory.mktemp("db")
    db_path = str(db_dir / "test.sqlite")

    # Patcher DB_PATH dans tous les modules
    import upload_spice
    import simulateur
    import metriques

    original_db_upload   = upload_spice.DB_PATH
    original_db_sim      = simulateur.DB_PATH

    upload_spice.DB_PATH = db_path
    simulateur.DB_PATH   = db_path

    # Initialiser la DB
    conn = sqlite3.connect(db_path)
    upload_spice.init_db(conn)
    conn.close()

    yield db_path

    # Restaurer
    upload_spice.DB_PATH = original_db_upload
    simulateur.DB_PATH   = original_db_sim


@pytest.fixture(scope="session")
def composant_1n4007(test_db_path):
    """Insère le composant 1N4007 dans la DB de test."""
    import upload_spice
    upload_spice.DB_PATH = test_db_path

    conn = sqlite3.connect(test_db_path)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT OR REPLACE INTO composants (nom, type, params_json, description)
        VALUES (?, ?, ?, ?)
    """, ("1N4007", "diode", json.dumps(TEST_PARAMS), "Test diode"))
    conn.commit()
    conn.close()
    return "1N4007"


# ─────────────────────────────────────────────────────────────────────────────
# Tests Métriques
# ─────────────────────────────────────────────────────────────────────────────

class TestMetriques:
    """Tests unitaires pour metriques.py"""

    def test_mae_identique(self):
        """MAE = 0 si les vecteurs sont identiques."""
        from metriques import calcul_mae
        y = np.array([1.0, 2.0, 3.0, 4.0])
        assert calcul_mae(y, y) == pytest.approx(0.0, abs=1e-15)

    def test_mae_connu(self):
        """MAE sur un cas connu."""
        from metriques import calcul_mae
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.1, 1.9, 3.2])
        # MAE = mean([0.1, 0.1, 0.2]) = 0.1333...
        assert calcul_mae(y_true, y_pred) == pytest.approx(0.1333, rel=1e-3)

    def test_rmse_connu(self):
        """RMSE sur un cas connu."""
        from metriques import calcul_rmse
        y_true = np.array([1.0, 2.0, 3.0])
        y_pred = np.array([1.0, 2.0, 4.0])
        # RMSE = sqrt(mean([0, 0, 1])) = sqrt(1/3)
        assert calcul_rmse(y_true, y_pred) == pytest.approx(np.sqrt(1/3), rel=1e-6)

    def test_erreur_max(self):
        """Erreur maximale correcte."""
        from metriques import calcul_erreur_max
        y_true = np.array([0.0, 0.0, 0.0])
        y_pred = np.array([0.1, 0.5, 0.2])
        assert calcul_erreur_max(y_true, y_pred) == pytest.approx(0.5, rel=1e-6)

    def test_erreur_rel_faible(self):
        """Erreur relative faible si prédiction proche."""
        from metriques import calcul_erreur_rel
        y_true = np.linspace(1e-6, 1.0, 100)
        y_pred = y_true * 1.01  # 1% d'erreur partout
        err = calcul_erreur_rel(y_true, y_pred)
        assert err < 2.0  # < 2%

    def test_verdict_pass_ia(self):
        """PASS quand erreur rel < 2%."""
        from metriques import verdict_pass_fail
        assert verdict_pass_fail(1.5, "ia") == "PASS"
        assert verdict_pass_fail(2.5, "ia") == "FAIL"

    def test_verdict_pass_hls(self):
        """PASS quand erreur rel < 5%."""
        from metriques import verdict_pass_fail
        assert verdict_pass_fail(4.9, "hls") == "PASS"
        assert verdict_pass_fail(5.1, "hls") == "FAIL"

    def test_r2_parfait(self):
        """R² = 1 si prédiction parfaite."""
        from metriques import calcul_r2
        y = np.linspace(0, 1, 50)
        assert calcul_r2(y, y) == pytest.approx(1.0, abs=1e-10)

    def test_toutes_metriques_retourne_dict(self):
        """toutes_metriques retourne les 5 clés attendues."""
        from metriques import toutes_metriques
        y = np.array([1.0, 2.0, 3.0])
        m = toutes_metriques(y, y * 1.01)
        assert set(m.keys()) == {"MAE", "RMSE", "E_max", "E_rel_%", "R2"}


# ─────────────────────────────────────────────────────────────────────────────
# Tests Upload / DB
# ─────────────────────────────────────────────────────────────────────────────

class TestUploadDB:
    """Tests pour upload_spice.py"""

    def test_init_db_cree_tables(self, test_db_path):
        """Les 4 tables sont créées après init_db."""
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {r[0] for r in cursor.fetchall()}
        conn.close()
        assert {"composants", "simulations", "modeles_ia", "modeles_hls"}.issubset(tables)

    def test_insert_composant(self, test_db_path, composant_1n4007):
        """Le composant 1N4007 est bien inséré."""
        import upload_spice
        upload_spice.DB_PATH = test_db_path
        data = upload_spice.get_composant("1N4007")
        assert data is not None
        assert data["nom"] == "1N4007"
        assert data["type"] == "diode"
        assert abs(data["parametres"]["IS"] - 7.62767e-9) < 1e-15

    def test_doublon_update(self, test_db_path):
        """Un deuxième insert sur le même nom met à jour sans erreur."""
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        params_new = TEST_PARAMS.copy()
        params_new["N"] = 1.9
        cursor.execute("""
            INSERT OR REPLACE INTO composants (nom, type, params_json, description)
            VALUES (?, ?, ?, ?)
        """, ("1N4007", "diode", json.dumps(params_new), "Updated"))
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM composants WHERE nom='1N4007'")
        count = cursor.fetchone()[0]
        conn.close()
        assert count == 1


# ─────────────────────────────────────────────────────────────────────────────
# Tests Simulateur
# ─────────────────────────────────────────────────────────────────────────────

class TestSimulateur:
    """Tests pour simulateur.py"""

    def test_courant_nul_a_zero_volt(self):
        """I(V=0) doit être ≈ 0."""
        from simulateur import _simuler_diode
        V = np.array([0.0])
        I = _simuler_diode(TEST_PARAMS, V)
        assert abs(I[0]) < 1e-6  # < 1µA

    def test_courant_positif_zone_directe(self):
        """I(V=0.7V) doit être positif et dans l'ordre mA-A."""
        from simulateur import _simuler_diode
        V = np.array([0.7])
        I = _simuler_diode(TEST_PARAMS, V)
        assert I[0] > 0
        assert 1e-4 < I[0] < 10  # entre 100µA et 10A

    def test_courant_faible_zone_inverse(self):
        """I(V=-1V) doit être ≈ -IS (très faible)."""
        from simulateur import _simuler_diode
        V = np.array([-1.0])
        I = _simuler_diode(TEST_PARAMS, V)
        assert I[0] < 0
        assert abs(I[0]) < 1e-6  # < 1µA

    def test_sweep_monotone_zone_directe(self):
        """La courbe doit être croissante en zone directe."""
        from simulateur import _simuler_diode
        V = np.linspace(0.3, 1.0, 50)
        I = _simuler_diode(TEST_PARAMS, V)
        # dI/dV > 0 en zone directe
        assert np.all(np.diff(I) >= 0), "Courbe non monotone en zone directe"

    def test_simulation_complete_shape(self, test_db_path, composant_1n4007):
        """simuler() retourne deux arrays de même longueur."""
        import simulateur
        simulateur.DB_PATH = test_db_path
        V, I = simulateur.simuler("1N4007", V_min=-2.0, V_max=1.0, n_points=200, force=True)
        assert len(V) == len(I)
        assert len(V) > 100

    def test_simulation_sauvegardee_en_db(self, test_db_path):
        """La simulation est bien persistée en base."""
        conn = sqlite3.connect(test_db_path)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.id FROM simulations s
            JOIN composants c ON s.composant_id = c.id
            WHERE c.nom = '1N4007'
        """)
        row = cursor.fetchone()
        conn.close()
        assert row is not None

    def test_charger_simulation_apres_save(self, test_db_path):
        """charger_simulation retourne les données persistées."""
        import simulateur
        simulateur.DB_PATH = test_db_path
        result = simulateur.charger_simulation("1N4007")
        assert result is not None
        V, I = result
        assert len(V) > 0


# ─────────────────────────────────────────────────────────────────────────────
# Tests Agent NLP
# ─────────────────────────────────────────────────────────────────────────────

class TestAgentNLP:
    """Tests pour la détection d'intentions dans agent_interface.py"""

    def setup_method(self):
        """Prépare le session state Streamlit simulé."""
        import agent_interface as ai
        # Simuler st.session_state
        class FakeSessionState:
            composant_actif = "1N4007"
            messages = []
        import streamlit as st
        if not hasattr(st, 'session_state') or st.session_state is None:
            pass  # Streamlit gère ça

    def _detecter(self, texte):
        """Helper pour détecter une intention."""
        import re
        from agent_interface import PATTERNS

        texte_norm = (texte.strip().lower()
                      .replace("é", "e").replace("è", "e").replace("ê", "e")
                      .replace("à", "a").replace("â", "a")
                      .replace("ç", "c").replace("î", "i"))

        for pattern, intention, _ in PATTERNS:
            m = re.search(pattern, texte_norm, re.IGNORECASE)
            if m:
                composant = m.group(1).strip().upper() if m.lastindex else "1N4007"
                return intention, composant
        return None, None

    def test_intention_courbe(self):
        intention, comp = self._detecter("courbe de 1N4007")
        assert intention == "courbe"
        assert comp == "1N4007"

    def test_intention_valider_ia(self):
        intention, comp = self._detecter("valide ia de 1N4007")
        assert intention == "valider_ia"
        assert "1N4007" in comp

    def test_intention_valider_hls(self):
        intention, comp = self._detecter("valide hls de 1N4007")
        assert intention == "valider_hls"

    def test_intention_validation_complete(self):
        intention, comp = self._detecter("validation complete de 1N4007")
        assert intention == "valider_complet"

    def test_intention_generer_ia(self):
        intention, comp = self._detecter("genere modele ia de 1N4007")
        assert intention == "generer_ia"

    def test_intention_generer_hls(self):
        intention, comp = self._detecter("genere hls de 1N4007")
        assert intention == "generer_hls"

    def test_intention_erreurs(self):
        intention, comp = self._detecter("erreur de 1N4007")
        assert intention == "erreurs"

    def test_intention_simuler(self):
        intention, comp = self._detecter("simule 1N4007")
        assert intention == "simuler"

    def test_intention_aide(self):
        intention, _ = self._detecter("aide")
        assert intention == "aide"

    def test_intention_inconnue(self):
        intention, _ = self._detecter("bonjour la plateforme")
        assert intention is None


# ─────────────────────────────────────────────────────────────────────────────
# Test d'intégration complet (pipeline end-to-end)
# ─────────────────────────────────────────────────────────────────────────────

class TestIntegration:
    """Test du pipeline complet : upload → simulate → métriques."""

    def test_pipeline_simulation_metriques(self, test_db_path, composant_1n4007):
        """
        Pipeline: simulation → génération de prédiction factice → métriques.
        Vérifie la cohérence des données du début à la fin.
        """
        import simulateur
        import metriques

        simulateur.DB_PATH = test_db_path

        # Simulation
        V, I = simulateur.simuler("1N4007", V_min=-1.0, V_max=1.0,
                                  n_points=300, force=True)
        assert len(V) > 0
        assert len(I) == len(V)

        # Prédiction factice (bruit 0.5%)
        np.random.seed(42)
        I_pred = I * (1 + np.random.normal(0, 0.005, len(I)))

        # Métriques
        m = metriques.toutes_metriques(I, I_pred)
        assert m["MAE"] >= 0
        assert m["RMSE"] >= m["MAE"]     # RMSE >= MAE toujours vrai
        assert m["E_max"] >= m["MAE"]    # E_max >= MAE toujours vrai
        assert 0 <= m["E_rel_%"] < 5.0  # < 5% avec bruit 0.5%
        assert 0.9 < m["R2"] <= 1.0     # R² proche de 1

    def test_courbe_diode_physiquement_coherente(self):
        """
        La courbe diode 1N4007 doit satisfaire les propriétés physiques:
        - I(0V) ≈ 0
        - I(0.7V) >> I(0.1V)  (zone directe exponentielle)
        - I(-1V) ≈ -IS < 0    (zone inverse)
        """
        from simulateur import _simuler_diode

        V_test = np.array([-1.0, 0.0, 0.1, 0.3, 0.5, 0.7, 1.0])
        I_test = _simuler_diode(TEST_PARAMS, V_test)

        # I(0V) ≈ 0
        assert abs(I_test[1]) < 1e-6

        # I croissant en zone directe
        assert I_test[2] < I_test[3] < I_test[4] < I_test[5] < I_test[6]

        # I(0.7V) dans la plage mA-centaines mA
        assert 1e-4 < I_test[5] < 5.0

        # Zone inverse : courant négatif et proche de -IS
        assert I_test[0] < 0
        assert abs(I_test[0]) < 1e-4  # courant de fuite très faible

    def test_tension_seuil_1n4007(self):
        """
        Pour la 1N4007, le seuil de conduction est autour de 0.6-0.75V.
        """
        from simulateur import _simuler_diode

        V = np.linspace(0.0, 1.0, 200)
        I = _simuler_diode(TEST_PARAMS, V)

        # Trouver V(I=1mA)
        idx_1ma = np.argmin(np.abs(I - 1e-3))
        V_seuil = V[idx_1ma]
        assert 0.5 < V_seuil < 0.9, f"Seuil inattendu: {V_seuil:.3f}V"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
