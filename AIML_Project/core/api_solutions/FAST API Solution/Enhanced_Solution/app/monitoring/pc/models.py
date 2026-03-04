"""
Performance Center - Pydantic Models
Standalone models for PC integration
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from enum import Enum


class PCConnectionRequest(BaseModel):
    """Request to connect to Performance Center and fetch results"""
    run_id: str = Field(..., description="Master run ID from RUN_MASTER")
    pc_run_id: str = Field(..., description="Performance Center run ID")
    pc_url: str = Field(..., description="Performance Center URL")
    pc_port: int = Field(default=8080, description="Performance Center port")
    pc_domain: str = Field(..., description="PC Domain")
    pc_project: str = Field(..., description="PC Project")
    username: str = Field(..., description="PC username")
    password: str = Field(..., description="PC password")
    test_set_name: Optional[str] = Field(None, description="Test set name")
    test_instance_id: Optional[str] = Field(None, description="Test instance ID")
    lob_name: str = Field(..., description="Line of Business")
    track: Optional[str] = Field(None, description="Track name")
    test_name: Optional[str] = Field(None, description="Test name")


class LRTransaction(BaseModel):
    """LoadRunner transaction statistics from summary.html"""
    transaction_name: str
    minimum_time: float
    average_time: float
    maximum_time: float
    std_deviation: float
    percentile_90: float
    percentile_95: Optional[float] = None
    percentile_99: Optional[float] = None
    pass_count: int
    fail_count: int
    stop_count: int = 0
    total_count: int
    pass_percentage: float
    throughput_tps: Optional[float] = None


class PCTestStatus(BaseModel):
    """Performance Center test status"""
    pc_run_id: str
    test_status: str
    collation_status: str
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    duration_seconds: Optional[int] = None


class PCFetchResponse(BaseModel):
    """Response from PC fetch operation"""
    success: bool
    run_id: str
    pc_run_id: str
    pc_test_id: int
    test_status: str
    collation_status: str
    transactions: List[LRTransaction]
    total_transactions: int
    passed_transactions: int
    failed_transactions: int
    average_response_time: float
    message: str


class PCResultsResponse(BaseModel):
    """Response for getting PC results from database"""
    success: bool
    run_id: str
    pc_run_id: str
    test_status: str
    collation_status: str
    total_transactions: int
    passed_transactions: int
    failed_transactions: int
    average_response_time: float
    transactions: List[LRTransaction]


class PCHealthStatus(BaseModel):
    """PC health status for landing page"""
    lob_name: str
    status: str
    recent_tests: int
    last_test_date: Optional[datetime] = None
    message: str
