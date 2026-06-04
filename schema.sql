-- Schema for JS-Python-Trade-Bridge
-- Generated from trade_bridge.sql with data rows removed.
-- Contains table definitions, primary keys, unique keys, indexes, and auto-increment attributes.

SET NAMES utf8mb4;

CREATE TABLE `ai_report` (
  `id` bigint NOT NULL,
  `symbol` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `start_date` date DEFAULT NULL,
  `end_date` date DEFAULT NULL,
  `timeframe` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `report_type` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'markdown',
  `report_markdown` longtext COLLATE utf8mb4_unicode_ci NOT NULL,
  `source` varchar(50) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'generated',
  `data_source` varchar(50) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `daily_price` (
  `id` bigint NOT NULL,
  `symbol` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `timeframe` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '1m',
  `ts` datetime NOT NULL,
  `open_price` decimal(12,4) NOT NULL,
  `high_price` decimal(12,4) NOT NULL,
  `low_price` decimal(12,4) NOT NULL,
  `close_price` decimal(12,4) NOT NULL,
  `volume` bigint NOT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `stocks` (
  `id` int NOT NULL,
  `symbol` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `market` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
CREATE TABLE `technical_snapshot` (
  `id` bigint NOT NULL,
  `symbol` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL,
  `timeframe` varchar(10) COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT '1m',
  `ts` datetime NOT NULL,
  `ma5` decimal(12,4) DEFAULT NULL,
  `ma20` decimal(12,4) DEFAULT NULL,
  `ma60` decimal(12,4) DEFAULT NULL,
  `ma120` decimal(12,4) DEFAULT NULL,
  `ema12` decimal(12,4) DEFAULT NULL,
  `ema26` decimal(12,4) DEFAULT NULL,
  `rsi14` decimal(8,4) DEFAULT NULL,
  `macd` decimal(12,4) DEFAULT NULL,
  `macd_signal` decimal(12,4) DEFAULT NULL,
  `macd_hist` decimal(12,4) DEFAULT NULL,
  `k_value` decimal(8,4) DEFAULT NULL,
  `d_value` decimal(8,4) DEFAULT NULL,
  `cci20` decimal(12,4) DEFAULT NULL,
  `atr14` decimal(12,4) DEFAULT NULL,
  `bb_mid` decimal(12,4) DEFAULT NULL,
  `bb_upper` decimal(12,4) DEFAULT NULL,
  `bb_lower` decimal(12,4) DEFAULT NULL,
  `bb_width` decimal(12,4) DEFAULT NULL,
  `vol_ma5` decimal(12,4) DEFAULT NULL,
  `vol_ma20` decimal(12,4) DEFAULT NULL,
  `support_1` decimal(12,4) DEFAULT NULL,
  `support_2` decimal(12,4) DEFAULT NULL,
  `support_3` decimal(12,4) DEFAULT NULL,
  `resist_1` decimal(12,4) DEFAULT NULL,
  `resist_2` decimal(12,4) DEFAULT NULL,
  `resist_3` decimal(12,4) DEFAULT NULL,
  `created_at` timestamp NULL DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Keys and indexes

ALTER TABLE `ai_report`
  ADD PRIMARY KEY (`id`),
  ADD KEY `idx_symbol_report` (`symbol`),
  ADD KEY `idx_created_at` (`created_at`);
ALTER TABLE `daily_price`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_symbol_timeframe_ts` (`symbol`,`timeframe`,`ts`),
  ADD KEY `idx_symbol` (`symbol`),
  ADD KEY `idx_ts` (`ts`),
  ADD KEY `idx_daily_symbol_timeframe_ts` (`symbol`,`timeframe`,`ts`);
ALTER TABLE `stocks`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `symbol` (`symbol`);
ALTER TABLE `technical_snapshot`
  ADD PRIMARY KEY (`id`),
  ADD UNIQUE KEY `uk_symbol_timeframe_ts_snapshot` (`symbol`,`timeframe`,`ts`),
  ADD KEY `idx_symbol_snapshot` (`symbol`),
  ADD KEY `idx_ts_snapshot` (`ts`),
  ADD KEY `idx_snapshot_symbol_timeframe_ts` (`symbol`,`timeframe`,`ts`);

-- Auto-increment columns

ALTER TABLE `ai_report`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT;
ALTER TABLE `daily_price`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT;
ALTER TABLE `stocks`
  MODIFY `id` int NOT NULL AUTO_INCREMENT;
ALTER TABLE `technical_snapshot`
  MODIFY `id` bigint NOT NULL AUTO_INCREMENT;

