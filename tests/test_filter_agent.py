"""Tests for the filter agent (document classification)"""
import pytest
from src.graph import evaluate_document_theme


def test_filter_agent_compliance_relevant():
    """Test that compliance documents are classified as 'Yes'"""
    text = """
    LDAR Survey Report
    Last survey: October 2023
    Methane emissions detected at separator unit
    High-bleed pneumatic devices in operation
    """
    result = evaluate_document_theme(text)
    assert "yes" in result.lower()


def test_filter_agent_non_compliance():
    """Test that non-compliance documents are classified as 'No'"""
    text = """
    FIFA World Cup 2022 Final
    Argentina vs France
    Lionel Messi scored two goals
    """
    result = evaluate_document_theme(text)
    assert "no" in result.lower()


def test_filter_agent_venting_flaring():
    """Test venting/flaring keywords trigger 'Yes'"""
    text = "Tank venting operations and flare routing requirements"
    result = evaluate_document_theme(text)
    assert "yes" in result.lower()