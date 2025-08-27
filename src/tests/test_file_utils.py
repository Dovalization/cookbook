"""
Unit tests for file utility functions with mocked filesystem operations.

Tests file handling utilities without making actual filesystem changes.
"""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, mock_open, Mock
from datetime import datetime

from shared.utils.files import (
    save_output,
    move_to_processed,
    add_timestamp_to_filename
)


class TestSaveOutput:
    """Test suite for save_output function."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path)

    @patch('shared.utils.files.config')
    def test_save_output_basic(self, mock_config, temp_dir: Path) -> None:
        """Test basic save_output functionality."""
        mock_config.OUTPUT_PATH = temp_dir
        
        content = "Test content for saving"
        filename = "test_output.txt"
        
        result_path = save_output(content, filename)
        
        assert result_path.exists()
        assert result_path.name == filename
        assert result_path.read_text() == content

    @patch('shared.utils.files.config')
    def test_save_output_with_subfolder(self, mock_config, temp_dir: Path) -> None:
        """Test save_output with subfolder creation."""
        mock_config.OUTPUT_PATH = temp_dir
        
        content = "Test content"
        filename = "output.txt"
        subfolder = "processed"
        
        result_path = save_output(content, filename, subfolder)
        
        assert result_path.parent.name == subfolder
        assert result_path.exists()
        assert result_path.read_text() == content
        assert (temp_dir / subfolder).exists()

    @patch('shared.utils.files.config')
    def test_save_output_duplicate_handling(self, mock_config, temp_dir: Path) -> None:
        """Test save_output handles duplicate filenames."""
        mock_config.OUTPUT_PATH = temp_dir
        
        filename = "duplicate.txt"
        
        # Create first file
        first_path = save_output("First content", filename)
        assert first_path.name == "duplicate.txt"
        
        # Create second file (should get renamed)
        second_path = save_output("Second content", filename)
        assert second_path.name == "duplicate-1.txt"
        
        # Create third file
        third_path = save_output("Third content", filename)
        assert third_path.name == "duplicate-2.txt"
        
        # Verify all files exist with correct content
        assert first_path.read_text() == "First content"
        assert second_path.read_text() == "Second content"
        assert third_path.read_text() == "Third content"

    @patch('shared.utils.files.config')
    def test_save_output_creates_parent_directories(self, mock_config, temp_dir: Path) -> None:
        """Test save_output creates parent directories if they don't exist."""
        mock_config.OUTPUT_PATH = temp_dir
        
        deep_subfolder = "level1/level2/level3"
        result_path = save_output("Content", "file.txt", deep_subfolder)
        
        assert result_path.exists()
        # Check that the deep path structure was created
        assert "level1" in str(result_path)
        assert "level2" in str(result_path)
        assert "level3" in str(result_path)
        assert result_path.read_text() == "Content"

    @patch('shared.utils.files.config')
    def test_save_output_with_file_extensions(self, mock_config, temp_dir: Path) -> None:
        """Test save_output handles file extensions correctly in duplicates."""
        mock_config.OUTPUT_PATH = temp_dir
        
        filename = "test.json"
        
        first_path = save_output('{"first": true}', filename)
        second_path = save_output('{"second": true}', filename)
        
        assert first_path.name == "test.json"
        assert second_path.name == "test-1.json"
        
        assert first_path.suffix == ".json"
        assert second_path.suffix == ".json"

    @patch('shared.utils.files.config')
    def test_save_output_empty_content(self, mock_config, temp_dir: Path) -> None:
        """Test save_output with empty content."""
        mock_config.OUTPUT_PATH = temp_dir
        
        result_path = save_output("", "empty.txt")
        
        assert result_path.exists()
        assert result_path.read_text() == ""

    @patch('shared.utils.files.config')
    def test_save_output_unicode_content(self, mock_config, temp_dir: Path) -> None:
        """Test save_output with unicode content."""
        mock_config.OUTPUT_PATH = temp_dir
        
        unicode_content = "Hello 🌍! Testing unicode: áéíóú 中文 🚀"
        result_path = save_output(unicode_content, "unicode.txt")
        
        assert result_path.exists()
        assert result_path.read_text(encoding='utf-8') == unicode_content

    @patch('shared.utils.files.config')
    @patch('builtins.open', side_effect=PermissionError("Permission denied"))
    def test_save_output_permission_error(self, mock_open_func, mock_config, temp_dir: Path) -> None:
        """Test save_output handles permission errors."""
        mock_config.OUTPUT_PATH = temp_dir
        
        with pytest.raises(PermissionError):
            save_output("Content", "restricted.txt")


class TestMoveToProcessed:
    """Test suite for move_to_processed function."""

    @pytest.fixture
    def temp_file(self):
        """Create a temporary file for testing."""
        temp_file = Path(tempfile.mktemp(suffix=".txt"))
        temp_file.write_text("Test file content")
        yield temp_file
        # Cleanup if file still exists
        if temp_file.exists():
            temp_file.unlink()

    def test_move_to_processed_basic(self, temp_file: Path) -> None:
        """Test basic move_to_processed functionality."""
        original_content = temp_file.read_text()
        
        moved_path = move_to_processed(temp_file)
        
        # Original file should be moved
        assert not temp_file.exists()
        
        # New file should exist in processed subfolder
        assert moved_path.exists()
        assert moved_path.parent.name == "processed"
        assert moved_path.name == temp_file.name
        assert moved_path.read_text() == original_content

    def test_move_to_processed_custom_subfolder(self, temp_file: Path) -> None:
        """Test move_to_processed with custom subfolder."""
        custom_subfolder = "archived"
        
        moved_path = move_to_processed(temp_file, custom_subfolder)
        
        assert not temp_file.exists()
        assert moved_path.exists()
        assert moved_path.parent.name == custom_subfolder

    def test_move_to_processed_duplicate_handling(self, temp_file: Path) -> None:
        """Test move_to_processed handles duplicates correctly."""
        # Create first processed version
        processed_dir = temp_file.parent / "processed"
        processed_dir.mkdir(exist_ok=True)
        existing_file = processed_dir / temp_file.name
        existing_file.write_text("Existing content")
        
        # Now move the temp file
        moved_path = move_to_processed(temp_file)
        
        # Should create a numbered version
        assert moved_path.name == f"{temp_file.stem}-1{temp_file.suffix}"
        assert existing_file.exists()  # Original processed file should remain
        assert moved_path.exists()  # New file should exist

    def test_move_to_processed_creates_processed_directory(self, temp_file: Path) -> None:
        """Test move_to_processed creates processed directory if it doesn't exist."""
        processed_dir = temp_file.parent / "processed"
        
        # Ensure processed directory doesn't exist
        if processed_dir.exists():
            shutil.rmtree(processed_dir)
        
        moved_path = move_to_processed(temp_file)
        
        assert processed_dir.exists()
        assert moved_path.exists()

    def test_move_to_processed_multiple_duplicates(self, temp_file: Path) -> None:
        """Test move_to_processed with multiple duplicates."""
        processed_dir = temp_file.parent / "processed"
        processed_dir.mkdir(exist_ok=True)
        
        base_name = temp_file.stem
        suffix = temp_file.suffix
        
        # Create several existing files
        for i in range(3):
            if i == 0:
                existing = processed_dir / temp_file.name
            else:
                existing = processed_dir / f"{base_name}-{i}{suffix}"
            existing.write_text(f"Existing content {i}")
        
        # Now move the temp file
        moved_path = move_to_processed(temp_file)
        
        # Should create the next available numbered version
        expected_name = f"{base_name}-3{suffix}"
        assert moved_path.name == expected_name

    @patch('shutil.move', side_effect=PermissionError("Permission denied"))
    def test_move_to_processed_permission_error(self, mock_move, temp_file: Path) -> None:
        """Test move_to_processed handles permission errors."""
        with pytest.raises(PermissionError):
            move_to_processed(temp_file)

    def test_move_to_processed_nonexistent_file(self) -> None:
        """Test move_to_processed with non-existent file."""
        nonexistent_file = Path("/tmp/this_file_does_not_exist.txt")
        
        with pytest.raises(FileNotFoundError):
            move_to_processed(nonexistent_file)


class TestAddTimestampToFilename:
    """Test suite for add_timestamp_to_filename function."""

    @patch('shared.utils.files.datetime')
    def test_add_timestamp_basic(self, mock_datetime) -> None:
        """Test basic timestamp addition to filename."""
        # Mock datetime.now() to return a fixed time
        mock_now = datetime(2024, 3, 15, 14, 30, 45)
        mock_datetime.now.return_value = mock_now
        
        filename = "document.txt"
        result = add_timestamp_to_filename(filename)
        
        expected = "20240315_143045_document.txt"
        assert result == expected

    @patch('shared.utils.files.datetime')
    def test_add_timestamp_no_extension(self, mock_datetime) -> None:
        """Test timestamp addition to filename without extension."""
        mock_now = datetime(2024, 1, 1, 9, 5, 30)
        mock_datetime.now.return_value = mock_now
        
        filename = "document_without_extension"
        result = add_timestamp_to_filename(filename)
        
        expected = "20240101_090530_document_without_extension"
        assert result == expected

    @patch('shared.utils.files.datetime')
    def test_add_timestamp_multiple_extensions(self, mock_datetime) -> None:
        """Test timestamp addition to filename with multiple extensions."""
        mock_now = datetime(2024, 12, 31, 23, 59, 59)
        mock_datetime.now.return_value = mock_now
        
        filename = "archive.tar.gz"
        result = add_timestamp_to_filename(filename)
        
        expected = "20241231_235959_archive.tar.gz"
        assert result == expected

    @patch('shared.utils.files.datetime')
    def test_add_timestamp_edge_cases(self, mock_datetime) -> None:
        """Test timestamp addition with edge case filenames."""
        mock_now = datetime(2024, 2, 29, 12, 0, 0)  # Leap year
        mock_datetime.now.return_value = mock_now
        
        test_cases = [
            ("", "20240229_120000_"),  # Path("").stem returns ""
            (".", "20240229_120000_"),  # Path(".").stem also returns ""
            (".hidden", "20240229_120000_.hidden"),
            ("file.", "20240229_120000_file."),
        ]
        
        for filename, expected in test_cases:
            result = add_timestamp_to_filename(filename)
            assert result == expected

    def test_add_timestamp_real_time(self) -> None:
        """Test timestamp addition uses real current time."""
        filename = "test.txt"
        result = add_timestamp_to_filename(filename)
        
        # Should match the pattern YYYYMMDD_HHMMSS_test.txt
        import re
        pattern = r'^\d{8}_\d{6}_test\.txt$'
        assert re.match(pattern, result)

    @patch('shared.utils.files.datetime')
    def test_timestamp_format_consistency(self, mock_datetime) -> None:
        """Test timestamp format is consistent and zero-padded."""
        # Test with single digits for month, day, hour, minute, second
        mock_now = datetime(2024, 1, 5, 8, 3, 7)
        mock_datetime.now.return_value = mock_now
        
        result = add_timestamp_to_filename("test.txt")
        
        # Should be zero-padded: 01, 05, 08, 03, 07
        expected = "20240105_080307_test.txt"
        assert result == expected


class TestFileUtilsIntegration:
    """Integration tests for file utilities working together."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for integration tests."""
        workspace = Path(tempfile.mkdtemp())
        yield workspace
        shutil.rmtree(workspace)

    @patch('shared.utils.files.config')
    def test_save_and_move_workflow(self, mock_config, temp_workspace: Path) -> None:
        """Test typical workflow of saving output and then moving it."""
        mock_config.OUTPUT_PATH = temp_workspace
        
        # Step 1: Save output
        content = "Processing complete!"
        saved_path = save_output(content, "result.txt")
        assert saved_path.exists()
        
        # Step 2: Move to processed
        moved_path = move_to_processed(saved_path)
        assert not saved_path.exists()
        assert moved_path.exists()
        assert moved_path.read_text() == content

    @patch('shared.utils.files.config')
    def test_timestamped_filename_workflow(self, mock_config, temp_workspace: Path) -> None:
        """Test workflow using timestamped filenames."""
        mock_config.OUTPUT_PATH = temp_workspace
        
        original_filename = "report.md"
        timestamped_filename = add_timestamp_to_filename(original_filename)
        
        # Save with timestamped name
        saved_path = save_output("# Report Content", timestamped_filename)
        
        # Verify timestamp is in the filename
        assert "report.md" in saved_path.name
        assert len(saved_path.name) > len(original_filename)
        
        # Move to processed
        moved_path = move_to_processed(saved_path)
        assert moved_path.parent.name == "processed"
        assert moved_path.read_text() == "# Report Content"