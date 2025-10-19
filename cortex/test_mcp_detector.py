#!/usr/bin/env python3
"""
Unit tests for MCP Detector
"""

import pytest
import json
import os
import tempfile
from pathlib import Path
from mcp_detector import MCPDetector, detect_and_config


class TestMCPDetection:
    """Test MCP type detection"""

    def test_detect_npx_package(self):
        """Test NPX package detection"""
        detector = MCPDetector()
        assert detector.detect_type("@openai/mcp") == "npx"
        assert detector.detect_type("@smithery/fetch") == "npx"
        assert detector.detect_type("@github/mcp") == "npx"

    def test_detect_http_url(self):
        """Test HTTP URL detection"""
        detector = MCPDetector()
        assert detector.detect_type("https://api.example.com/mcp") == "http"
        assert detector.detect_type("http://localhost:3000/mcp") == "http"

    def test_detect_python_script(self):
        """Test Python script detection"""
        detector = MCPDetector()
        # Create temporary Python file
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            f.write(b"#!/usr/bin/env python3\n")
            temp_path = f.name

        try:
            assert detector.detect_type(temp_path) == "python"
        finally:
            os.unlink(temp_path)

    def test_detect_nodejs_script(self):
        """Test Node.js script detection"""
        detector = MCPDetector()
        # Create temporary Node.js file
        with tempfile.NamedTemporaryFile(suffix=".js", delete=False) as f:
            f.write(b"#!/usr/bin/env node\n")
            temp_path = f.name

        try:
            assert detector.detect_type(temp_path) == "nodejs"
        finally:
            os.unlink(temp_path)

    def test_detect_binary_executable(self):
        """Test binary executable detection"""
        detector = MCPDetector()
        # Create temporary executable file
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"#!/bin/bash\necho 'test'\n")
            temp_path = f.name

        try:
            os.chmod(temp_path, 0o755)
            assert detector.detect_type(temp_path) == "binary"
        finally:
            os.unlink(temp_path)

    def test_invalid_type_detection(self):
        """Test invalid input raises error"""
        detector = MCPDetector()
        with pytest.raises(ValueError):
            detector.detect_type("invalid_input")


class TestNPXPackageParsing:
    """Test NPX package parsing"""

    def test_parse_standard_package(self):
        """Test parsing standard @org/package format"""
        detector = MCPDetector()
        org, version = detector.parse_npx_package("@openai/mcp")
        assert org == "openai/mcp"
        assert version == "latest"

    def test_parse_package_with_version(self):
        """Test parsing package with explicit version"""
        detector = MCPDetector()
        org, version = detector.parse_npx_package("@smithery/fetch@1.2.3")
        assert org == "smithery/fetch"
        assert version == "1.2.3"

    def test_parse_invalid_package(self):
        """Test parsing invalid package format"""
        detector = MCPDetector()
        with pytest.raises(ValueError):
            detector.parse_npx_package("invalid-package")


class TestProviderNameExtraction:
    """Test provider name extraction"""

    def test_extract_name_from_npx(self):
        """Test extracting name from NPX package"""
        detector = MCPDetector()
        name = detector.extract_provider_name("@openai/mcp", "npx")
        assert name == "mcp"

    def test_extract_name_from_http(self):
        """Test extracting name from HTTP URL"""
        detector = MCPDetector()
        name = detector.extract_provider_name("https://api.smithery.ai/mcp", "http")
        assert name == "smithery"

    def test_extract_name_from_python(self):
        """Test extracting name from Python path"""
        detector = MCPDetector()
        name = detector.extract_provider_name("/path/to/script.py", "python")
        assert name == "script"

    def test_extract_name_from_binary(self):
        """Test extracting name from binary path"""
        detector = MCPDetector()
        name = detector.extract_provider_name("/usr/local/bin/my-mcp", "binary")
        assert name == "my-mcp"


class TestConfigGeneration:
    """Test MCP config generation"""

    def test_generate_npx_config(self):
        """Test NPX config generation"""
        detector = MCPDetector()
        config = detector.build_config(
            "@openai/mcp",
            credentials={"OPENAI_API_KEY": "sk-xxx"},
            description="OpenAI MCP",
            tools=["chat", "embeddings"],
            category="ai",
        )

        assert "mcp" in config
        assert config["mcp"]["command"] == "npx"
        assert "--openai-api-key" in config["mcp"]["args"]
        assert "sk-xxx" in config["mcp"]["args"]
        assert config["mcp"]["category"] == "ai"
        assert config["mcp"]["tools"] == ["chat", "embeddings"]

    def test_generate_http_config(self):
        """Test HTTP config generation"""
        detector = MCPDetector()
        config = detector.build_config(
            "https://api.example.com/mcp",
            description="Example HTTP Service",
        )

        assert "example" in config
        assert config["example"]["command"] == "curl"
        assert "-s" in config["example"]["args"]
        assert "https://api.example.com/mcp" in config["example"]["args"]

    def test_generate_python_config(self):
        """Test Python config generation"""
        detector = MCPDetector()
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            f.write(b"#!/usr/bin/env python3\n")
            temp_path = f.name

        try:
            config = detector.build_config(
                temp_path,
                credentials={"DATABASE_URL": "postgresql://..."},
                description="Custom Python MCP",
                tools=["query", "execute"],
                category="database",
            )

            script_name = Path(temp_path).stem
            assert script_name in config
            assert config[script_name]["command"] == "python3"
            assert config[script_name]["args"] == [temp_path]
            assert config[script_name]["env"]["DATABASE_URL"] == "postgresql://..."
            assert config[script_name]["category"] == "database"

        finally:
            os.unlink(temp_path)

    def test_generate_binary_config(self):
        """Test binary config generation"""
        detector = MCPDetector()
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"#!/bin/bash\necho 'test'\n")
            temp_path = f.name

        try:
            os.chmod(temp_path, 0o755)
            config = detector.build_config(
                temp_path,
                description="Custom Binary MCP",
            )

            binary_name = Path(temp_path).stem
            assert binary_name in config
            assert config[binary_name]["command"] == temp_path
            assert config[binary_name]["args"] == []

        finally:
            os.unlink(temp_path)


class TestCategoryInference:
    """Test category inference"""

    def test_infer_ai_category(self):
        """Test inferring AI category"""
        detector = MCPDetector()
        assert detector._infer_category("openai", "npx") == "ai"
        assert detector._infer_category("anthropic", "npx") == "ai"
        assert detector._infer_category("huggingface", "npx") == "ai"

    def test_infer_database_category(self):
        """Test inferring database category"""
        detector = MCPDetector()
        assert detector._infer_category("postgres", "npx") == "database"
        assert detector._infer_category("mongodb", "npx") == "database"
        assert detector._infer_category("redis", "npx") == "database"

    def test_infer_communication_category(self):
        """Test inferring communication category"""
        detector = MCPDetector()
        assert detector._infer_category("slack", "npx") == "communication"
        assert detector._infer_category("discord", "npx") == "communication"
        assert detector._infer_category("telegram", "npx") == "communication"

    def test_infer_default_category(self):
        """Test default category when no match"""
        detector = MCPDetector()
        assert detector._infer_category("unknown-service", "npx") == "utility"


class TestConvenienceFunction:
    """Test convenience function"""

    def test_convenience_function_npx(self):
        """Test detect_and_config convenience function"""
        config = detect_and_config(
            "@openai/mcp",
            credentials={"OPENAI_API_KEY": "sk-xxx"},
            tools=["chat"],
        )

        assert "mcp" in config
        assert config["mcp"]["command"] == "npx"

    def test_convenience_function_http(self):
        """Test convenience function with HTTP"""
        config = detect_and_config("https://api.example.com/mcp")

        assert "example" in config
        assert config["example"]["command"] == "curl"


class TestCredentialsHandling:
    """Test credentials handling"""

    def test_npx_credentials_as_flags(self):
        """Test NPX credentials converted to command flags"""
        detector = MCPDetector()
        config = detector.build_config(
            "@openai/mcp",
            credentials={
                "OPENAI_API_KEY": "sk-xxx",
                "ORG_ID": "org-123",
            },
        )

        args = config["mcp"]["args"]
        assert "--openai-api-key" in args
        assert "--org-id" in args
        assert "sk-xxx" in args
        assert "org-123" in args

    def test_python_credentials_as_env(self):
        """Test Python credentials set as environment variables"""
        detector = MCPDetector()
        with tempfile.NamedTemporaryFile(suffix=".py", delete=False) as f:
            f.write(b"#!/usr/bin/env python3\n")
            temp_path = f.name

        try:
            config = detector.build_config(
                temp_path,
                credentials={
                    "DATABASE_URL": "postgresql://...",
                    "API_KEY": "secret-key",
                },
            )

            env = config[Path(temp_path).stem]["env"]
            assert env["DATABASE_URL"] == "postgresql://..."
            assert env["API_KEY"] == "secret-key"

        finally:
            os.unlink(temp_path)

    def test_empty_credentials(self):
        """Test handling empty credentials"""
        detector = MCPDetector()
        config = detector.build_config("@openai/mcp", credentials={})

        assert "mcp" in config
        assert config["mcp"]["command"] == "npx"


class TestErrorHandling:
    """Test error handling"""

    def test_missing_python_file(self):
        """Test error when Python file doesn't exist"""
        detector = MCPDetector()
        with pytest.raises(ValueError, match="not found"):
            detector.build_config("/nonexistent/path.py")

    def test_missing_binary_file(self):
        """Test error when binary doesn't exist"""
        detector = MCPDetector()
        with pytest.raises(ValueError, match="not found"):
            detector.build_config("/nonexistent/binary")

    def test_non_executable_binary(self):
        """Test error when binary is not executable"""
        detector = MCPDetector()
        with tempfile.NamedTemporaryFile(delete=False) as f:
            f.write(b"not executable")
            temp_path = f.name

        try:
            with pytest.raises(ValueError, match="not executable"):
                detector.build_config(temp_path)
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
