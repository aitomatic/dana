"""Tests for SpinnerComponent phase-based text updates."""

from rich.spinner import Spinner

from dana.cli.components.spinner import SpinnerComponent


class TestSpinnerInit:
    """Test constructor and defaults."""

    def test_default_style(self) -> None:
        spinner = SpinnerComponent()
        assert isinstance(spinner.spinner, Spinner)

    def test_custom_style(self) -> None:
        spinner = SpinnerComponent(style="line")
        assert isinstance(spinner.spinner, Spinner)

    def test_not_running_by_default(self) -> None:
        spinner = SpinnerComponent()
        assert spinner.running is False


class TestStartStop:
    """Test start/stop lifecycle."""

    def test_start_sets_running(self) -> None:
        spinner = SpinnerComponent()
        spinner.start()
        assert spinner.running is True

    def test_stop_clears_running(self) -> None:
        spinner = SpinnerComponent()
        spinner.start()
        spinner.stop()
        assert spinner.running is False

    def test_stop_when_already_stopped(self) -> None:
        spinner = SpinnerComponent()
        spinner.stop()
        assert spinner.running is False


class TestUpdatePhase:
    """Test text updates for each STAR phase."""

    def test_see_phase(self) -> None:
        spinner = SpinnerComponent()
        spinner.update_phase("SEE")
        assert spinner.text == "Processing..."

    def test_think_phase(self) -> None:
        spinner = SpinnerComponent()
        spinner.update_phase("THINK")
        assert spinner.text == "Thinking..."

    def test_act_phase_no_tools(self) -> None:
        spinner = SpinnerComponent()
        spinner.update_phase("ACT")
        assert spinner.text == "Executing..."

    def test_act_phase_with_single_tool(self) -> None:
        spinner = SpinnerComponent()
        spinner.update_phase("ACT", context={"tools": ["bash"]})
        assert spinner.text == "Executing bash..."

    def test_act_phase_with_multiple_tools(self) -> None:
        spinner = SpinnerComponent()
        spinner.update_phase("ACT", context={"tools": ["bash", "read_file", "grep"]})
        assert spinner.text == "Executing bash, read_file, grep..."

    def test_act_phase_with_empty_tools_list(self) -> None:
        spinner = SpinnerComponent()
        spinner.update_phase("ACT", context={"tools": []})
        assert spinner.text == "Executing..."

    def test_reflect_phase(self) -> None:
        spinner = SpinnerComponent()
        spinner.update_phase("REFLECT")
        assert spinner.text == "Reflecting..."

    def test_unknown_phase_uses_phase_name(self) -> None:
        spinner = SpinnerComponent()
        spinner.update_phase("CUSTOM")
        assert spinner.text == "CUSTOM..."

    def test_update_phase_no_context(self) -> None:
        spinner = SpinnerComponent()
        spinner.update_phase("SEE", context=None)
        assert spinner.text == "Processing..."

    def test_phase_transitions(self) -> None:
        """Verify spinner text updates across phase transitions."""
        spinner = SpinnerComponent()
        spinner.update_phase("SEE")
        assert spinner.text == "Processing..."
        spinner.update_phase("THINK")
        assert spinner.text == "Thinking..."
        spinner.update_phase("ACT", context={"tools": ["bash"]})
        assert spinner.text == "Executing bash..."
        spinner.update_phase("REFLECT")
        assert spinner.text == "Reflecting..."


class TestCharCounting:
    """Test character counting and token estimation."""

    def test_initial_char_count_zero(self) -> None:
        spinner = SpinnerComponent()
        assert spinner.estimated_tokens_text == "~0 tokens"

    def test_increment_chars(self) -> None:
        spinner = SpinnerComponent()
        spinner.increment_chars(400)
        assert spinner.estimated_tokens_text == "~100 tokens"

    def test_increment_chars_multiple(self) -> None:
        spinner = SpinnerComponent()
        spinner.increment_chars(2000)
        spinner.increment_chars(2000)
        assert spinner.estimated_tokens_text == "~1.0k tokens"

    def test_start_resets_char_count(self) -> None:
        spinner = SpinnerComponent()
        spinner.increment_chars(8000)
        spinner.start()
        assert spinner.estimated_tokens_text == "~0 tokens"

    def test_k_suffix_formatting(self) -> None:
        spinner = SpinnerComponent()
        spinner.increment_chars(4800)  # 1200 tokens -> ~1.2k
        assert spinner.estimated_tokens_text == "~1.2k tokens"

    def test_m_suffix_formatting(self) -> None:
        spinner = SpinnerComponent()
        spinner.increment_chars(4_000_000)  # 1M tokens
        assert spinner.estimated_tokens_text == "~1.0M tokens"

    def test_small_count_no_suffix(self) -> None:
        spinner = SpinnerComponent()
        spinner.increment_chars(200)  # 50 tokens
        assert spinner.estimated_tokens_text == "~50 tokens"


class TestImport:
    """Test package imports."""

    def test_import_from_components_package(self) -> None:
        from dana.cli.components import SpinnerComponent as Imported

        assert Imported is SpinnerComponent
