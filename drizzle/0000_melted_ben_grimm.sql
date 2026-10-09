CREATE TABLE `implementation_events` (
	`sequence` integer PRIMARY KEY AUTOINCREMENT NOT NULL,
	`event_key` text NOT NULL,
	`recorded_at` text NOT NULL,
	`source_id` text NOT NULL,
	`payload` text NOT NULL,
	`hash` text NOT NULL,
	`previous_hash` text
);
--> statement-breakpoint
CREATE UNIQUE INDEX `implementation_event_key` ON `implementation_events` (`event_key`);--> statement-breakpoint
CREATE UNIQUE INDEX `implementation_event_hash` ON `implementation_events` (`hash`);