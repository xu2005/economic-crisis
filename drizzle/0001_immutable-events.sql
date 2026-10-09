CREATE TRIGGER implementation_no_update BEFORE UPDATE ON implementation_events BEGIN SELECT RAISE(ABORT, 'append only: update forbidden'); END;
--> statement-breakpoint
CREATE TRIGGER implementation_no_delete BEFORE DELETE ON implementation_events BEGIN SELECT RAISE(ABORT, 'append only: delete forbidden'); END;
