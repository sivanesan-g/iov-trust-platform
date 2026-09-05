// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract TrustRegistry {
    struct TrustRecord {
        string vehicleId;
        uint256 trustScore;
        string predictionLabel;
        uint256 confidence;
        string shard;
        uint256 timestamp;
        string status;
    }

    mapping(string => TrustRecord[]) private vehicleHistory;
    mapping(string => uint256) public latestTrustScore;

    event TrustUpdated(
        string vehicleId,
        uint256 trustScore,
        string predictionLabel,
        uint256 confidence,
        string shard,
        uint256 timestamp,
        string status
    );

    function updateTrust(
        string memory vehicleId,
        uint256 trustScore,
        string memory predictionLabel,
        uint256 confidence,
        string memory shard,
        string memory status
    ) public {
        TrustRecord memory rec = TrustRecord({
            vehicleId: vehicleId,
            trustScore: trustScore,
            predictionLabel: predictionLabel,
            confidence: confidence,
            shard: shard,
            timestamp: block.timestamp,
            status: status
        });

        vehicleHistory[vehicleId].push(rec);
        latestTrustScore[vehicleId] = trustScore;

        emit TrustUpdated(
            vehicleId,
            trustScore,
            predictionLabel,
            confidence,
            shard,
            block.timestamp,
            status
        );
    }

    function getHistoryCount(string memory vehicleId) public view returns (uint256) {
        return vehicleHistory[vehicleId].length;
    }

    function getLatestTrust(string memory vehicleId) public view returns (uint256) {
        return latestTrustScore[vehicleId];
    }
}