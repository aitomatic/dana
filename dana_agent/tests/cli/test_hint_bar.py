"""Tests for HintBarComponent contextual hints."""

from rich.text import Text

from dana.cli.components.hint_bar import HintBarComponent


class TestHintBarRender:
    """Test hint bar rendering for different states."""

    def test_processing_shows_interrupt_hint(self) -> None:
        bar = HintBarComponent()
        result = bar.render(is_processing=True)
        assert isinstance(result, Text)
        assert "esc to interrupt" in result.plain

    def test_processing_with_results(self) -> None:
        bar = HintBarComponent()
        result = bar.render(has_results=True, is_processing=True)
        assert isinstance(result, Text)
        assert "esc to interrupt" in result.plain

    def test_idle_no_results(self) -> None:
        bar = HintBarComponent()
        result = bar.render(has_results=False, is_processing=False)
        assert result is None

    def test_idle_with_results(self) -> None:
        bar = HintBarComponent()
        result = bar.render(has_results=True, is_processing=False)
        assert isinstance(result, Text)
        assert "navigate results" in result.plain


class TestImport:
    """Test package imports."""

    def test_import_from_components_package(self) -> None:
        from dana.cli.components import HintBarComponent as Imported

        assert Imported is HintBarComponent
