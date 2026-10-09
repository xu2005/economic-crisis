import {sqliteTable,integer,text,uniqueIndex} from 'drizzle-orm/sqlite-core';
export const implementationEvents=sqliteTable('implementation_events',{
 sequence:integer('sequence').primaryKey({autoIncrement:true}),
 eventKey:text('event_key').notNull(),recordedAt:text('recorded_at').notNull(),sourceId:text('source_id').notNull(),payload:text('payload').notNull(),hash:text('hash').notNull(),previousHash:text('previous_hash'),
},t=>[uniqueIndex('implementation_event_key').on(t.eventKey),uniqueIndex('implementation_event_hash').on(t.hash)]);
