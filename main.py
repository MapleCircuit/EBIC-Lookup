from collections import namedtuple, deque
import mysql.connector
from operator import itemgetter
import subprocess as sp
import sys
import shutil
from pathlib import Path
import re
import pickle
import multiprocessing


# Right now this only mutes include errors that don't break everything
CLEAN_PRINT = True

RAMDISK = "/dev/shm"
CPUS = 8
linux_directory = Path('linux')

multi_proc = False

def emergency_shutdown():
	mf.clear_all_version()
	sys.exit(0)
	return

class _MyBreak(Exception): pass

########### DB UTILS ###########
def connect_sql():
	# Connect to DB
	return mysql.connector.connect(host="localhost", user="root", password="Passe123", database="test")

def set_db():
	db = []
	db.append(connect_sql())
	db.append(db[0].cursor())
	execdb(db, "SET SESSION sql_mode = 'NO_AUTO_VALUE_ON_ZERO';")
	execdb(db, "SET GLOBAL max_allowed_packet = 1073741824;")
	return db

def unset_db(db):
	db[1].close()
	db[0].close()
	return []

def execdb(db, sql, data=None):
	if data:
		if type(data[0]) is tuple:
			db[1].executemany(sql, data)
			return db[0].commit()
	db[1].execute(sql, data)
	return db[0].commit()

def selectdb(db, sql):
	db[1].execute(sql)
	return
########### DB UTILS ###########

class Great_Processor(deque):
	def __init__(self):
		global multi_proc
		multi_proc = False
		self.vid = 0
		self.loggin = []
		self.version_name = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
		self.vid = 0
		self.manager = None
		self.shared_set_list = None

	def __getstate__(self):
		# Copy the object's state from self.__dict__ which contains
		# all our instance attributes. Always use the dict.copy()
		# method to avoid modifying the original state.
		state = self.__dict__.copy()
		# Remove the unpicklable entries.
		del state['loggin']
		del state['manager']
		del state['change_list']
		return state

	def create_new_vid(self, name):
		self.old_version_name = self.version_name
		self.version_name = name
		self.old_vid = self.vid
		self.vid = m_v_main.set(None, name).vid
		m_v_main.insert_set()
		m_v_main.clear_fetch()
		return

	def create_new_tid(self, s_vid, e_vid=0):
		self.tid = m_time.set(None, s_vid, e_vid).tid
		return

	def generate_change_list(self):
		#if self.old_vid == 0:
			#self.change_list = list(map(lambda x: f"A\t{x}" , git_file_list(self.version_name).splitlines()))
		#else:
		self.change_list = git_change_list(self.old_version_name, self.version_name)
		return self.change_list

	def processing_dirs(self):
		# Based on dirs
		command = [
			"find",
			f"{mf.version_dict[self.version_name]}",
			"-type",
			"d",
			"!",
			"-type",
			"l",
			"-printf",
			"%P\\n"
		]
		# the [1:] is for the blank line that this sh** command produce at the start
		dir_list = sp.run(command, capture_output=True, text=True).stdout.splitlines()[1:]

		if self.old_vid != 0:
			command = [
				"find",
				f"{mf.version_dict[self.old_version_name]}",
				"-type",
				"d",
				"!",
				"-type",
				"l",
				"-printf",
				"%P\\n"
			]

			old_dir_list = set(sp.run(command, capture_output=True, text=True).stdout.splitlines()[1:])
			dir_list = set(dir_list)
			new_dir_list = (dir_list - old_dir_list)


			# Unchanged dirs
			for single_dir in (dir_list - (dir_list - old_dir_list)):
				if m_file_name.get(m_file_name.fname(single_dir)) is None:
					new_dir_list.add(single_dir)
					print("Unchanged dirs: fname is None")
					print(single_dir)
					continue
				# Get old_bf
				old_bf = m_bridge_file.get(
					m_bridge_file.vid(gp.old_vid),
					m_bridge_file.fnid( m_file_name.get(m_file_name.fname(single_dir)).fnid )
				)
				m_bridge_file(gp.vid, old_bf.fnid, old_bf.fid)

			# New dirs
			for single_dir in new_dir_list:
				dir_file_name = m_file_name.get_set(m_file_name.fname(single_dir))
				dir_file = m_file(None, gp.tid, 1, "A", 0)
				m_bridge_file(gp.vid, dir_file_name.fnid, dir_file.fid)
			# Deleted dirs
			for single_dir in (old_dir_list - dir_list):
				# Get old_bf
				if m_file_name.get(m_file_name.fname(single_dir)) is None:
					print("Deleted dirs: fname is None")
					print(single_dir)
					continue
				old_bf = m_bridge_file.get(
					m_bridge_file.vid(gp.old_vid),
					m_bridge_file.fnid( m_file_name.get(m_file_name.fname(single_dir)).fnid )
				)
				if old_bf is None:
					print("Deleted dirs: old_bf is None")
					print(single_dir)
					print(m_file_name.get(m_file_name.fname(single_dir)))
					continue
				# 0 New TID for old FILE
				dir_time = m_time(
					None,
					m_time.get( m_time.tid( m_file.get( m_file.fid(old_bf.fid) ).tid ) ).vid_s,
					gp.old_vid
				)
				# 1 Update old FILE
				m_file.update(
					old_bf.fid,
					dir_time.tid,
					None,
					None,
					"R"
				)

		else:
			# If VID = 1, we need all dirs to be added
			for single_dir in dir_list:
				dir_file_name = m_file_name.get_set(m_file_name.fname(single_dir))
				dir_file = m_file(None, gp.tid, 1, "A", 0)
				m_bridge_file(gp.vid, dir_file_name.fnid, dir_file.fid)
		return

	def preload_fnid(self):
		# Based on change
		for changed_file in map(lambda x: x.split("\t")[-1], self.change_list):
			m_file_name.get_set(m_file_name.fname(changed_file))
		return

	def processing_changes(self):
		global multi_proc
		multi_proc = True
		self.manager = multiprocessing.Manager()
		self.shared_set_list = self.manager.list()
		processes = []

		try:
			for x in range(CPUS-1):
				if x == (CPUS-2):
					processes.append(multiprocessing.Process(target=file_processing, args=(len(gp.change_list)//int(CPUS-1)*x, None)))
				else:
					processes.append(multiprocessing.Process(target=file_processing, args=(len(gp.change_list)//int(CPUS-1)*x, len(gp.change_list)//int(CPUS-1)*(x+1))))
				processes[-1].start()

			for fp_instance in processes:
				fp_instance.join()
		except Exception as e:
			print("Error in gp.processing_changes()")
			print(e)
			emergency_shutdown()

		del processes
		multi_proc = False
		return

	def processing_unchanges(self):
		if self.old_vid == 0:
			return
		full_set = set(git_file_list(self.version_name).splitlines())
		changed_set = set(map(lambda x: x.split("\t")[-1], filter(lambda x: not x.startswith("D"), self.change_list)))
		unchanged_set = (full_set - changed_set)
		deleted_set = set(map(lambda x: x.split("\t")[-1], filter(lambda x: x.startswith("D"), self.change_list)))
		old_full_set = set(git_file_list(self.old_version_name).splitlines())
		forgotten_delete = ((old_full_set - full_set) - deleted_set)
		if forgotten_delete:
			print("There seems to be forgotten deletes... Processing...")
			file_processing(0, 0, list(map(lambda x: f"D\t{x}" , forgotten_delete)))

		forgotten_new = ((full_set - old_full_set) - changed_set)
		if forgotten_new:
			print("There seems to be forgotten_new...")
			print(forgotten_new)
			print("There seems to be forgotten_new...")

		for unchanged in unchanged_set:
			old_bf = m_bridge_file.get(
				m_bridge_file.vid(gp.old_vid),
				m_bridge_file.fnid( m_file_name.get(m_file_name.fname(unchanged)).fnid )
			)
			if old_bf is None:
				print("processing_unchanges: old_bf is None")
				print(unchanged)
				print(m_file_name.get(m_file_name.fname(unchanged)))
				continue
			m_bridge_file(gp.vid, old_bf.fnid, old_bf.fid)
		return

	def push_set_to_main(self):
		self.shared_set_list.append(pickle.dumps(gp))
		return

	def set(self, *args):
		self.append(args)
		return

	def execute(self):
		global multi_proc
		multi_proc = False
		while self:
			x = []
			for item in self.popleft():
				while item.__class__.__name__ == "Delayed_Executor":
					item = item.process(x)
				x.append(item)
			#print(f"execute() results:{x}")
		return

	def execute_all(self):
		print("Great_Processor.execute() start")
		self.execute()
		count = 0
		if len(self.shared_set_list) != CPUS-1:
			print(f"You have {len(self.shared_set_list)} set_list. We need {CPUS-1}!!! Exiting now!")
			emergency_shutdown()
		for remote_gp in self.shared_set_list:
			print(f"gp:{count}")
			pickle.loads(remote_gp).execute()
			count += 1

		print("Great_Processor.execute_all() done")
		return

	def insert_all(self):
		for table in self.loggin:
			table.insert_set()
			table.insert_update()
		return

	def clear_fetch_all(self):
		for table in self.loggin:
			table.clear_fetch()
		return

	def print_all_set(self):
		for table in self.loggin:
			print(table.set_table)
		return

gp = Great_Processor()

class Referenced_Element:
	"""
	Get the values in prior item in array, works in tandem with GP.
	"""
	def __init__(self, offset=None, attribute=None):
		self.offset = offset
		self.stored_attribute = attribute

	def __setstate__(self, state):
		self.offset = state.get("offset", None)
		self.stored_attribute = state.get("stored_attribute", None) #Needed for unpickleling

	def __getitem__(self, key):
		return Referenced_Element(key)

	def __getattr__(self, name):
		return Referenced_Element(self.offset, name)

	def get_value(self, current_list):
		if self.offset < 0:
			output = current_list[(self.offset+len(current_list))]
		else:
			output = current_list[self.offset]
		if self.stored_attribute:
			output = getattr(output, self.stored_attribute)
		return output
X = Referenced_Element()

class Delayed_Executor:
	"""
	Preserves the values in set/update command, works in tandem with GP.
	"""
	def __init__(self, table, action, item):
		self.table = table
		self.action = action
		self.item = item

	def process(self, array):
		return getattr(globals()[self.table], self.action)(self.item, array)



class Table:
	#example: table("time", (("tid", "INT", "NOT NULL", "AUTO_INCREMENT"),("vid_s", "INT", "NOT NULL"),("vid_e", "INT", "NOT NULL")), ("tid",), (("vid_s", "v_main", "vid"),("vid_e", "v_main", "vid")), (0, 0, 0) )
	def __init__(self, table_name: str, columns: tuple, primary: tuple, foreign=None, initial_insert=None, no_dupplicate=False, get_list=False):
		self.table_name = table_name
		self.init_columns = columns
		self.init_primary = primary
		self.init_foreign = foreign
		self.initial_insert = initial_insert
		self.no_dupplicate = no_dupplicate
		self.auto_increment = False
		self.get_list = get_list
		gp.loggin.append(self)
		return


	class Column_Class:
		def __init__(self, table_name: str, column_id: int):
			self.table_name = table_name
			self.column_id = column_id
			return

		def __call__(self, value=None):
			return (self.table_name, self.column_id, value)

	def create_table(self):
		self.reference_name = {}
		temp_id = 0
		temp_arr = []
		temp_sql = ""
		for col in self.init_columns:
			self.reference_name[col[0]] = temp_id
			setattr(self, f"{col[0]}", self.Column_Class(self.table_name, temp_id))
			temp_arr.append(col[0])

			if "AUTO_INCREMENT" in col:
				self.auto_increment = True

			temp_sql += f"{" ".join(map(str, col))},"

			temp_id += 1

		self.namedtuple = namedtuple(self.table_name, temp_arr)
		self.namedtuple.__qualname__ = f"{self.table_name}.namedtuple" #Needed for pickleling
		self.columns = tuple(temp_arr)

		temp_arr_primary = []
		temp_sql += f" PRIMARY KEY ("
		for keys in self.init_primary:
			temp_sql += f"{keys},"
			temp_arr_primary.append(temp_arr.index(keys))

		self.primary_key = tuple(temp_arr_primary)
		del temp_arr, temp_arr_primary


		self.sql_set = f"INSERT INTO {self.table_name} VALUES ({("%s," * len(self.columns))[:-1]})"
		key_update_sql = ""

		print(self.columns)
		print("-----------------")

		for column in self.columns:
			if column not in itemgetter(*self.primary_key)(self.columns):
				key_update_sql += f"{column} = VALUES({column}), "
		self.sql_update = f"INSERT INTO {self.table_name} ({', '.join(map(str, self.columns))}) VALUES ({("%s," * len(self.columns))[:-1]}) ON DUPLICATE KEY UPDATE {key_update_sql[:-2]}"


		temp_sql = f"{temp_sql[:-1]}),"

		if self.init_foreign:
			for keys in self.init_foreign:
				temp_sql += f" FOREIGN KEY ({keys[0]}) REFERENCES {keys[1]}({keys[2]}),"

		db = set_db()
		execdb(db, f"CREATE TABLE {self.table_name} ({temp_sql[:-1]} );")
		del temp_sql

		if self.initial_insert:
			execdb(db, f"INSERT INTO {self.table_name} VALUES ({("%s," * temp_id)[:-1]})", self.initial_insert)
		del temp_id

		unset_db(db)
		return


	def clear_fetch(self):
		self.optimized_table = {}

		db = set_db()
		selectdb(db, f"SELECT * FROM {self.table_name}")

		self.current_table = {}

		for row in db[1].fetchall():
			self.current_table[itemgetter(*self.primary_key)(row)] = self.namedtuple(*row)

		if self.auto_increment:
			self.no_dupplicate_dict = {}
			if self.current_table:
				self.set_index = max(self.current_table) + 1
			else:
				self.set_index = 1

		self.set_table = {}
		self.update_table = {}

		unset_db(db)
		return

	def gen_optimized_table(self, *columns):
		key_group = tuple(map(itemgetter(1), columns))

		self.optimized_table[key_group] = {}

		if self.get_list:
			for row in self.current_table.values():
				if self.optimized_table[key_group].get(itemgetter(*key_group)(row)):
					self.optimized_table[key_group][itemgetter(*key_group)(row)].append(itemgetter(*self.primary_key)(row))
				else:
					self.optimized_table[key_group][itemgetter(*key_group)(row)] = list(itemgetter(*self.primary_key)(row))
		else:
			for row in self.current_table.values():
				self.optimized_table[key_group][itemgetter(*key_group)(row)] = itemgetter(*self.primary_key)(row)

		return

	def get(self, *columns):
		if not columns:
			return None

		key_group = tuple(map(itemgetter(1), columns))
		values = tuple(map(itemgetter(2), columns))

		if len(values) == 1:
			values = values[0]

		if key_group == self.primary_key:
			return self.current_table.get(values)
		else:
			if key_group in self.optimized_table:
				if self.get_list:
					get_array = []
					if (keys := self.optimized_table[key_group].get(values)):
						for key in self.optimized_table[key_group].get(values):
							if (query_result := self.current_table.get(key)):
								get_array.append(query_result)
						if get_array:
							return get_array
					return None
				else:
					return self.current_table.get(self.optimized_table[key_group].get(values))
			else:
				print(f"Error with: {columns}")
				print("Revert to for loop for get()")
				for row in self.current_table.values():
					if itemgetter(*key_group)(row) == values:
						return row
				return None

	def __call__(self, *item):
		return self.set(*item)

	def set(self, *item):
		if multi_proc:
			return Delayed_Executor(self.table_name, "dset", item)

		if type(item[0]) == tuple:
			item = item[0]

		# IF YOU HAVE AN ERROR LIKE(TypeError: m_file_name.__new__() takes 3 positional arguments but 4 were given) THAT MEANS THAT YOU SHOULD USE GET_SET
		item = self.namedtuple(*item)
		if (self.auto_increment) and (item[0] is None):
			if self.no_dupplicate:
				if (no_dup_key := self.no_dupplicate_dict.get(item[1:])) is not None:
					return self.set_table[no_dup_key]

				while self.set_index in self.set_table:
					self.set_index += 1

				item = (self.set_index,) + item[1:]
				self.no_dupplicate_dict[item[1:]] = self.set_index
				self.set_index += 1

			else:
				while self.set_index in self.set_table:
					self.set_index += 1

				item = (self.set_index,) + item[1:]
				self.set_index += 1
		else:
			if itemgetter(*self.primary_key)(item) in self.set_table:
				return self.set_table[itemgetter(*self.primary_key)(item)]

		self.set_table[itemgetter(*self.primary_key)(item)] = self.namedtuple(*item)
		return self.namedtuple(*item)

	def dset(self, items, array):
		output = []
		for item in items:
			if item.__class__.__name__ == "Referenced_Element":
				output.append(item.get_value(array))
			else:
				output.append(item)
		return self.set(*output)

	def get_set(self, *columns):
		temp = self.get(*columns)

		if temp is not None:
			return temp

		temp_arr = [None] * len(self.init_columns)
		for item in columns:
			temp_arr[item[1]] = item[2]
		return self.set(*temp_arr)

	# CAN RETURN NONE IF NO ITEM AT PRIMARY KEY
	def update(self, *item):
		if multi_proc:
			return Delayed_Executor(self.table_name, "dupdate", item)

		if type(item[0]) == tuple:
			item = item[0]

		current_item = self.current_table.get(itemgetter(*self.primary_key)(item))
		new_item = []

		if current_item is None:
			return None

		for part_item in item:
			if part_item is None:
				part_item = current_item[len(new_item)]
			new_item.append(part_item)

		self.update_table[itemgetter(*self.primary_key)(new_item)] = self.namedtuple(*new_item)
		return self.namedtuple(*new_item)

	def dupdate(self, items, array):
		output = []
		for item in items:
			if item.__class__.__name__ == "Referenced_Element":
				output.append(item.get_value(array))
			else:
				output.append(item)
		return self.update(*output)

	def insert_set(self):
		if not self.set_table:
			return
		db = set_db()
		try:
			execdb(db, self.sql_set, tuple(tuple(col) for col in self.set_table.values()))
		except Exception as e:
			print(f"Error happend while insert_set() in table:{self.table_name}")
			print(db[1].statement)
			print(e)
			emergency_shutdown()
		unset_db(db)
		del self.set_table
		self.set_table = {}
		return

	def insert_update(self):
		if not self.update_table:
			return
		db = set_db()
		try:
			key_update_sql = ""
			for column in self.reference_name:
				if column not in self.primary_key:
					key_update_sql += f"{column} = VALUES({column}), "
			execdb(db, self.sql_update, tuple(tuple(col) for col in self.update_table.values()))
		except Exception as e:
			print(f"Error happend while insert_update() in table:{self.table_name}")
			print(db[1].statement)
			print(e)
			emergency_shutdown()
		unset_db(db)
		del self.update_table
		self.update_table = {}
		return

##################################
# DB STRUCTURE

m_v_main = Table("m_v_main", (("vid", "INT", "NOT NULL", "AUTO_INCREMENT"),("vname", "VARCHAR(32)", "NOT NULL", "COLLATE utf8mb4_bin")), ("vid",), None, ((0,"latest"),) )

m_file_name = Table("m_file_name", (("fnid", "INT", "NOT NULL", "AUTO_INCREMENT"),("fname", "VARCHAR(255)", "NOT NULL", "COLLATE utf8mb4_bin")), ("fnid",), None, ((0,""),) , True )


# Name of table
m_time = Table("m_time",
	# Each columns, AUTO_INCREMENT is detected (if provided)
	(("tid", "INT", "NOT NULL", "AUTO_INCREMENT"),("vid_s", "INT", "NOT NULL"),("vid_e", "INT", "NOT NULL")),
	# Primary key(s)
	("tid",),
	# Foreign key(s)
	(("vid_s", "m_v_main", "vid"),("vid_e", "m_v_main", "vid")),
	# Initial insert(s)
	((0,0,0),),
	# Values (omitting the primary key) must be unique?
	True
)


m_file = Table("m_file", (("fid", "INT", "NOT NULL", "AUTO_INCREMENT"),("tid", "INT", "NOT NULL"),("ftype", "TINYINT", "UNSIGNED", "NOT NULL"),("s_stat", "CHAR(1)", "NOT NULL"),("e_stat", "CHAR(1)", "NOT NULL")), ("fid",), (("tid", "m_time", "tid"),), ((0,0,0,0,0)) )

m_bridge_file = Table("m_bridge_file", (("vid", "INT", "NOT NULL"),("fnid", "INT", "NOT NULL"),("fid", "INT", "NOT NULL")), ("vid","fnid"), (("vid", "m_v_main", "vid"),("fnid","m_file_name","fnid"),("fid","m_file","fid")), None)

m_moved_file = Table("m_moved_file", (("s_fid", "INT", "NOT NULL"),("e_fid", "INT", "NOT NULL")), ("s_fid","e_fid"), (("s_fid", "m_file", "fid"),("e_fid", "m_file", "fid")), None)

m_include = Table("m_include", (("iid", "INT", "NOT NULL", "AUTO_INCREMENT"),("tid", "INT", "NOT NULL")), ("iid",), (("tid", "m_time", "tid"),), ((0,0),), False )

m_include_content = Table("m_include_content", (("iid", "INT", "NOT NULL"),("rank", "INT", "NOT NULL"),("fnid", "INT", "NOT NULL")), ("iid","rank"), (("iid", "m_include", "iid"),("fnid","m_file_name","fnid")), None )

m_bridge_include = Table("m_bridge_include", (("fid", "INT", "NOT NULL"),("iid", "INT", "NOT NULL")), ("fid","iid"), (("fid","m_file","fid"),("iid", "m_include", "iid")), None)

m_tag_name = Table("m_tag_name", (("tnid", "INT", "NOT NULL", "AUTO_INCREMENT"),("tname", "VARCHAR(255)", "NOT NULL", "COLLATE utf8mb4_bin")), ("tnid",), None, ((0,""),), True)

m_tag = Table("m_tag", (("tgid", "INT", "NOT NULL", "AUTO_INCREMENT"),("tid", "INT", "NOT NULL"),("ttype", "TINYINT", "UNSIGNED", "NOT NULL"),("tnid", "INT", "NOT NULL")), ("tgid",), (("tid","m_time","tid"),("tnid","m_tag_name","tnid")), ((0,0,0,0),))

m_tag_content = Table("m_tag_content", (("tgid", "INT", "NOT NULL"),("rank", "INT", "NOT NULL"),("mtgid", "INT", "NOT NULL")), ("tgid","rank"), (("tgid","m_tag","tgid"),("mtgid","m_tag","tgid")), None, False, True)

m_line = Table("m_line", (("lnid", "INT", "NOT NULL", "AUTO_INCREMENT"),("ln_s", "INT", "UNSIGNED", "NOT NULL"),("ln_e", "INT", "UNSIGNED", "NOT NULL")), ("lnid",), None, ((0,4294967295,0),), True)

m_bridge_tag = Table("m_bridge_tag", (("fid", "INT", "NOT NULL"),("tgid", "INT", "NOT NULL"),("lnid", "INT", "NOT NULL")), ("fid","tgid"), (("fid","m_file","fid"),("tgid","m_tag","tgid"),("lnid","m_line","lnid")), None, False, True)

m_ident_name = Table("m_ident_name", (("ident_nid", "INT", "UNSIGNED", "NOT NULL", "AUTO_INCREMENT"),("iname", "VARCHAR(255)", "NOT NULL", "COLLATE utf8mb4_bin")), ("ident_nid",), None, ((0,""),), True)

m_ident_email = Table("m_ident_email", (("ident_eid", "INT", "UNSIGNED", "NOT NULL", "AUTO_INCREMENT"),("email", "VARCHAR(255)", "NOT NULL", "COLLATE utf8mb4_bin")), ("ident_eid",), None, ((0,""),), True)

m_ident = Table("m_ident", (("ident_id", "INT", "UNSIGNED", "NOT NULL", "AUTO_INCREMENT"),("s_vid", "INT", "NOT NULL"),("ident_nid", "INT", "UNSIGNED", "NOT NULL"),("ident_eid", "INT", "UNSIGNED", "NOT NULL")), ("ident_id",), (("s_vid","m_v_main","vid"),("ident_nid","m_ident_name","ident_nid"),("ident_eid","m_ident_email","ident_eid")), ((0,0,0,0),))

m_bridge_ident_name = Table("m_bridge_ident_name", (("ident_id", "INT", "UNSIGNED", "NOT NULL"),("ident_nid", "INT", "UNSIGNED", "NOT NULL")), ("ident_id","ident_nid"), (("ident_id","m_ident","ident_id"),("ident_nid","m_ident_name","ident_nid")), None)

m_bridge_ident_email = Table("m_bridge_ident_email", (("ident_id", "INT", "UNSIGNED", "NOT NULL"),("ident_eid", "INT", "UNSIGNED", "NOT NULL")), ("ident_id","ident_eid"), (("ident_id","m_ident","ident_id"),("ident_eid","m_ident_email","ident_eid")), None)

m_commit = Table("m_commit", (("cid", "INT", "NOT NULL", "AUTO_INCREMENT"),("hash", "CHAR(40)", "NOT NULL"),("timestamp", "BIGINT", "UNSIGNED", "NOT NULL"),("ident_id", "INT", "UNSIGNED", "NOT NULL")), ("cid",), (("ident_id","m_ident","ident_id"),), ((0,0,0,0),), True)

m_bridge_commit_file = Table("m_bridge_commit_file", (("fid", "INT", "NOT NULL"),("cid", "INT", "NOT NULL")), ("fid","cid"), (("fid","m_file","fid"),("cid","m_commit","cid")), None)

m_bridge_commit_tag = Table("m_bridge_commit_tag", (("tgid", "INT", "NOT NULL"),("cid", "INT", "NOT NULL")), ("tgid","cid"), (("tgid","m_tag","tgid"),("cid","m_commit","cid")), None)

m_kconfig_name = Table("m_kconfig_name", (("knid", "INT", "NOT NULL", "AUTO_INCREMENT"),("kname", "VARCHAR(255)", "NOT NULL", "COLLATE utf8mb4_bin")), ("knid",), None, ((0,""),), True)

m_kconfig_display = Table("m_kconfig_display", (("kdid", "INT", "NOT NULL", "AUTO_INCREMENT"),("kdisplay", "VARCHAR(255)", "NOT NULL", "COLLATE utf8mb4_bin")), ("kdid",), None, ((0,""),), True)

m_kconfig = Table("m_kconfig", (("kid", "INT", "NOT NULL", "AUTO_INCREMENT"),("tid", "INT", "NOT NULL"),("ktype", "TINYINT", "UNSIGNED", "NOT NULL"),("knid", "INT", "NOT NULL"),("kdid", "INT", "NOT NULL")), ("kid",), (("tid", "m_time", "tid"),("knid","m_kconfig_name","knid"),("kdid","m_kconfig_display","kdid")), ((0,0,0,0,0)) )
#ktype:
#bool=1
#tristate=2
#string=3
#hex=4
#int=5

m_kconfig_source = Table("m_kconfig_source", (("ksid", "INT", "NOT NULL", "AUTO_INCREMENT"),("fnid", "INT", "NOT NULL")), ("ksid",), (("fnid","m_file_name","fnid"),), ((0,0),))

m_kconfig_order = Table("m_kconfig_order", (("koid", "INT", "NOT NULL", "AUTO_INCREMENT"),("tid", "INT", "NOT NULL")), ("koid",), (("tid","m_time","tid"),), ((0,0),))

m_kconfig_order_content = Table("m_kconfig_order_content", (("koid", "INT", "NOT NULL"),("rank", "INT", "NOT NULL"),("kotype", "TINYINT", "UNSIGNED", "NOT NULL")), ("koid",), (("koid","m_kconfig_order","koid"),), None)
#kotype:
#config=1
#menuconfig=2
#choice=3
#endchoice=4
#comment=5
#menu=6
#endmenu=7
#if=8
#endif=9
#source=10

m_bridge_kconfig = Table("m_bridge_kconfig", (("fid", "INT", "NOT NULL"),("koid", "INT", "NOT NULL")), ("fid","koid"), (("fid","m_file","fid"),("koid","m_kconfig_order","koid")), None)

# DB STRUCTURE END
##################################

def initialize_db():
	print("Creating m_v_main")
	m_v_main.create_table()

	print("Creating m_file_name")
	m_file_name.create_table()

	print("Creating m_time")
	m_time.create_table()

	print("Creating m_file")
	m_file.create_table()

	print("Creating m_bridge_file")
	m_bridge_file.create_table()

	print("Creating m_moved_file")
	m_moved_file.create_table()

	print("Creating m_include")
	m_include.create_table()

	print("Creating m_include_content")
	m_include_content.create_table()

	print("Creating m_bridge_include")
	m_bridge_include.create_table()

	print("Creating m_tag_name")
	m_tag_name.create_table()

	print("Creating m_tag")
	m_tag.create_table()

	print("Creating m_tag_content")
	m_tag_content.create_table()

	print("Creating m_line")
	m_line.create_table()

	print("Creating m_bridge_tag")
	m_bridge_tag.create_table()

	print("Creating m_ident_name")
	m_ident_name.create_table()

	print("Creating m_ident_email")
	m_ident_email.create_table()

	print("Creating m_ident")
	m_ident.create_table()

	print("Creating m_bridge_ident_name")
	m_bridge_ident_name.create_table()

	print("Creating m_bridge_ident_email")
	m_bridge_ident_email.create_table()

	print("Creating m_commit")
	m_commit.create_table()

	print("Creating m_bridge_commit_file")
	m_bridge_commit_file.create_table()

	print("Creating m_bridge_commit_tag")
	m_bridge_commit_tag.create_table()

	print("Creating m_kconfig_name")
	m_kconfig_name.create_table()

	print("Creating m_kconfig_display")
	m_kconfig_display.create_table()

	print("Creating m_kconfig")
	m_kconfig.create_table()

	print("Creating m_kconfig_source")
	m_kconfig_source.create_table()

	print("Creating m_kconfig_order")
	m_kconfig_order.create_table()

	print("Creating m_kconfig_order_content")
	m_kconfig_order_content.create_table()

	print("Creating m_bridge_kconfig")
	m_bridge_kconfig.create_table()
	return


class Master_File:
	def __init__(self):
		self.version_dict = {}
		self.file_dict = {}
		self.parse_tag = re.compile(r'CONFIG_|operator ')
		self.parse_tag_typename = re.compile(r'typename:')
		self.parse_tag_struct = re.compile(r'struct:')
		self.parse_tag_anon = re.compile(r'__anon')


	def add_version(self, version_name=None):
		if version_name is None:
			version_name=gp.version_name
		self.version_dict[version_name] = git_clone(version_name)
		self.file_dict[version_name] = {}

	def trim_version(self, keep=2):
		if len(self.version_dict) > keep:
			print("Removing old version_dict")
			shutil.rmtree(self.version_dict[next(iter(self.version_dict))])
			del self.version_dict[next(iter(self.version_dict))]
			del self.file_dict[next(iter(self.file_dict))]
			return 1
		return 0

	def clear_all_version(self):
		for item in self.version_dict:
			shutil.rmtree(self.version_dict[item])
		return

	def get_file(self, file_path, version=None):
		if version is None:
			version=gp.version_name
		if version not in self.version_dict:
			command = [
				"git",
				"--git-dir=linux/.git",
				"show",
				f"{version}:{file_path}"
			]
			raw_file = sp.run(command, capture_output=True, text=True, encoding='latin-1')
			return raw_file.stdout
		else:
			if file_path not in self.file_dict[version]:
				self.file_dict[version][file_path] = Path(f"{self.version_dict[version]}/{file_path}").read_text(encoding='latin-1')
		return self.file_dict[version][file_path]


	def get_includes(self, file_path, version=None):
		temp_type = type_check(file_path)
		if not (temp_type == 2 or temp_type == 3):
			return False

		if version is None:
			version=gp.version_name

		try:
			if (current_file := self.get_file(file_path, version)) is f"fatal: path '{file_path}' does not exist in '{version}'":
				return False
		except FileNotFoundError:
			return False

		results = tuple(filter(lambda x: x.startswith("#include"), current_file.splitlines()))
		if results:
			temp_arr = []
			final_arr = []
			for item in results:
				try:
					match item[9:10]:
						case "<":
							temp_arr.append("include/" + item[10:item.find(">")])
						case '"':
							temp_arr.append(f"{Path(file_path).parent}/" + item[10:(item[10:].find('"')+10)])
						case _:
							if not CLEAN_PRINT:
								print(f"Unrecognised include: {item}")
				except:
					print(f"Unrecognised include causing an error: {item}")
			for item in filter(str.strip, temp_arr):
				path_arr = []
				dotdot = 0
				for chunk in item.split("/")[::-1]:
					if chunk == "..":
						dotdot += 1
					elif dotdot > 0:
						dotdot -= 1
					else:
						path_arr.append(chunk)
				final_arr.append("/".join(path_arr[::-1]))
			if final_arr:
				return final_arr
		return False

	def get_tags(self, file_path, version=None):
		temp_type = type_check(file_path)
		if not (temp_type == 2 or temp_type == 3):
			return False

		if version is None:
			version=gp.version_name

		command = [
			"ctags",
			"--sort=no",
			"--output-format=xref",
			"--fields=+neK",
			'--_xformat=%N %n %{end} %K %{typeref}',
			"--kinds-c=+p+x",
			"--extras=-{anonymous}",
			"-o", "-",
			f"{mf.version_dict[version]}/{file_path}"
		]

		tagss = sp.run(command, capture_output=True, text=True)
		tags = tagss.stdout.splitlines()
		#if file_path == "tools/usb/ffs-test.c":
		#	with open(f"{mf.version_dict[version]}/{file_path}", "r") as file:
		#		content = file.read()
		#		print(content)
		#	print("THIS IS HELL1")
		#	print(tags)
		#	print("THIS IS HELL")
		#	print(tagss.stderr)
		# BASED DEPARTMENT @436f6c74

		result_tags = []

		for i, tag in enumerate(tags):
			if re.match(self.parse_tag, tag):
				continue
			result_tags.append(tag.split(" ", 4))
			try:
				result_tags[-1][3] = ctags_type(result_tags[-1][3])
				result_tags[-1][1] = int(result_tags[-1][1])
				if result_tags[-1][2] == '':
					result_tags[-1][2] = result_tags[-1][1]
				else:
					result_tags[-1][2] = int(result_tags[-1][2])


				# When we have a struct:"7" we should:
				# 1. detect the following members
				# 2. correct the fact that they would be a type member and (Maybe) set them to the actual type (Unsure think about it more but we should probably have an idea of what the fuck it is)
				# 3. Record in a seperate table that links between the "Main" struct and the "Member" tag.
				# GOOD LUCK

				# parsing of the type of a member ############################################## UNFINISHED ¯\_(ツ)_/¯
				#if result_tags[-1][3] == 6:
				#	if re.match(result_tags[-1][4], self.parse_tag_typename):
				#		result_tags[-1][4] = result_tags[-1][9:]
				#	elif re.match(result_tags[-1][4], self.parse_tag_struct):
				#		result_tags[-1][4] = result_tags[-1][7:]
				#		if re.match(result_tags[-1][4], self.parse_tag_anon):
				#			result_tags[-1][4] = None
			except IndexError:
				print("mf.get_tags get demolished by this tag:")
				print(result_tags[-1])
				del result_tags[-1]
				continue
		if not result_tags:
			return None

		return result_tags



mf = Master_File()

########### GIT UTILS ###########
def git_change_list(old_vn, vn):
	command = [
		"git",
		"--git-dir=linux/.git",
		"diff",
		f"{old_vn}",
		f"{vn}",
		"--name-status"
	]

	raw_file_list = sp.run(command, capture_output=True, text=True)
	return raw_file_list.stdout.splitlines()

def git_clone(version):
	temp_path = create_temp_dir()

	command = [
		"git",
		"clone",
		f"{linux_directory}",
		"--branch",
		f"{version}",
		f"{temp_path}",
		"-c advice.detachedHead=false"
	]

	sp.run(command)
	shutil.rmtree(f"{temp_path}/.git")
	return temp_path

def git_file_list(version):
	command = [
		"git",
		"--git-dir=linux/.git",
		"ls-tree",
		"-r",
		"--name-only",
		f"{version}"
	]
	raw_file = sp.run(command, capture_output=True, text=True)
	return raw_file.stdout

########### GIT UTILS ###########

def create_temp_dir():
	command = [
		"mktemp",
		"-d",
		"-p",
		f"{RAMDISK}",
		"kernel-parser.XXXXXX"
	]
	output = sp.run(command, capture_output=True, text=True)
	return output.stdout.strip()

def type_check(name):
	#dirs are for 1
	if name.endswith((".c")):
		return 2
	elif name.endswith((".h")):
		return 3
	elif name.endswith(("Kconfig")):
		return 4
	else:
		return 0

def ctags_type(type):
	match type:
		case "macro":
			return 1
		case "enumerator":
			return 2
		case "function":
			return 3
		case "enum":
			return 4
		case "header":
			return 5
		case "member":
			return 6
		case "struct":
			return 7
		case "typedef":
			return 8
		case "union":
			return 9
		case "variable":
			return 10
		case "prototype":
			return 11
		case "externvar":
			return 12
		case "class":
			return 13
		case "slot":
			return 14
		case "signal":
			return 15
		print("did not find ctag kind: " + type)
	return 0



def file_processing(start, end=None, override_list=None):
	global multi_proc
	if override_list:
		changed_files = override_list
		multi_proc = True
	else:
		if end is None:
			changed_files = gp.change_list[start:]
		else:
			changed_files = gp.change_list[start:end]
		#print(changed_files, flush=True)
	for changed_file in changed_files:
		cut_file = tuple(changed_file.split("\t"))
		cs = []
		try:
			match cut_file[0][0]:
				case "D":
					# DELETE
					# Get old_bf
					old_bf = m_bridge_file.get(
						m_bridge_file.vid(gp.old_vid),
						m_bridge_file.fnid( m_file_name.get( m_file_name.fname(cut_file[1]) ).fnid )
					)
					if old_bf is None:
						print("case \"D\": old_bf is None")
						print(cut_file[1])
						print(m_file_name.get(m_file_name.fname(cut_file[1])))
						continue
					# 0 New TID for FILE
					cs.append(m_time(
						None,
						m_time.get( m_time.tid( m_file.get( m_file.fid(old_bf.fid) ).tid ) ).vid_s,
						gp.old_vid
					))
					# 1 Update FILE
					cs.append(m_file.update(
						old_bf.fid,
						X[0].tid,
						None,
						None,
						"D"
					))

					# Check if iid existed
					if (temp_iid := m_bridge_include.get(m_bridge_include.fid(old_bf.fid))):
						# 2 New TID for INCLUDE
						cs.append(m_time(
							None,
							m_time.get( m_time.tid( m_include.get( m_include.iid(temp_iid.iid) ).tid ) ).vid_s,
							gp.old_vid
						))
						# 3 Update INCLUDE
						cs.append(m_include.update(temp_iid.iid, X[2].tid))
					#EXIT INCLUDES

					if (old_tags := m_bridge_tag.get(m_bridge_tag.fid(old_bf.fid))):
						for old_tag in old_tags:
							if old_tag is None:
								continue
							# ? New TID for TAG
							cs.append(m_time(
								None,
								m_time.get( m_time.tid( m_tag.get( m_tag.tgid(old_tag.tgid) ).tid ) ).vid_s,
								gp.old_vid
							))
							# ? Update TAG
							cs.append(m_tag.update(old_tag.tgid, X[-1].tid, None, None))

					# temp = get_file(db, vid - 1, cut_file[1])
					# if temp is not None:
					# 	execdb(db, f"UPDATE file SET tid = {tid_dict.get(temp[1])}, ftype = {temp[2]}, s_stat = '{temp[3]}', e_stat = 'D' WHERE fid = {temp[0]};")
					# 	if temp[2] == 2 or temp[2] == 3:
					# 		if ENABLE_INCLUDE:
					# 			selectdb(db, f"SELECT bi.iid, i.tid FROM include AS i INNER JOIN bridge_include AS bi ON bi.iid = i.iid WHERE fid = {temp[0]} LIMIT 1")
					# 			iid_tid = db[1].fetchone()
					# 			if iid_tid is not None:
					# 				execdb(db, f"UPDATE include SET tid = {tid_dict.get(iid_tid[1])} WHERE iid = {iid_tid[0]};")
					# 		if ENABLE_CTAGS:
					# 			selectdb(db, f"SELECT bt.tgid, t.tid FROM tag AS t INNER JOIN bridge_tag AS bt ON bt.tgid = t.tgid WHERE fid = {temp[0]}")
					# 			tgid_tids = db[1].fetchall()
					# 			insert_tag = ""
					# 			insert_tag_where = ""
					# 			for tgid_tid in tgid_tids:
					# 				insert_tag += f"WHEN {tgid_tid[0]} THEN {tid_dict.get(tgid_tid[1])} "
					# 				insert_tag_where += f"{tgid_tid[0]}, "
					# 			if insert_tag != "":
					# 				execdb(db, f"UPDATE tag SET tid = CASE tgid {insert_tag}END WHERE tgid IN ({insert_tag_where[:-2]});")
				case "R":
					if cut_file[0][1:4] == "100":
						# Exact Moved
						# Get old_bf
						old_bf = m_bridge_file.get(
							m_bridge_file.vid(gp.old_vid),
							m_bridge_file.fnid( m_file_name.get( m_file_name.fname(cut_file[1]) ).fnid )
						)
						if old_bf is None:
							print("case \"R\": if 100: old_bf is None")
							print(cut_file[1])
							print(m_file_name.get(m_file_name.fname(cut_file[1])))
							raise _MyBreak
						# 0 New TID for old FILE
						cs.append(m_time(
							None,
							m_time.get( m_time.tid( m_file.get( m_file.fid(old_bf.fid) ).tid ) ).vid_s,
							gp.old_vid
						))
						# 1 Update old FILE
						cs.append(m_file.update(
							old_bf.fid,
							X[0].tid,
							None,
							None,
							"R"
						))

						# 2 Check if FNAME exist/Create FNAME
						cs.append(m_file_name.get_set(m_file_name.fname(cut_file[2])))
						# 3 Create FILE
						cs.append(m_file(None, gp.tid, type_check(cut_file[2]), "R", 0))
						# 4 Create BRIDGE FILE
						cs.append(m_bridge_file(gp.vid, X[2].fnid, X[3].fid))

						# 5 Create MOVED FILE
						cs.append(m_moved_file(old_bf.fid, X[3].fid))

						# Check if iid existed
						if (temp_iid := m_bridge_include.get(m_bridge_include.fid(old_bf.fid))):
							# 6 Create BRIDGE INCLUDE
							cs.append(m_bridge_include(X[3].fid, temp_iid.iid))
						#EXIT INCLUDES



					# 	# Correct old file
					# 	temp = get_file(db, vid - 1, cut_file[1])
					# 	if temp is not None:
					# 		execdb(db, f"UPDATE file SET tid = {tid_dict.get(temp[1])}, ftype = {temp[2]}, s_stat = '{temp[3]}', e_stat = 'R' WHERE fid = {temp[0]};")
		#
					# 	# Create new fnid/file/bridge_file/moved_file
					# 	temp_fnid = fnid_dict.get(cut_file[2])
					# 	execdb(db, f"INSERT INTO file (tid, ftype, s_stat, e_stat) VALUES ({s_tid}, {type_check(cut_file[2])}, 'R', 0);")
					# 	new_fid = db[1].lastrowid
					# 	execdb(db, f"INSERT INTO bridge_file (vid, fnid, fid) VALUES ({vid}, {temp_fnid}, {new_fid});")
					# 	if temp is not None:
					# 		execdb(db, f"INSERT INTO moved_file (s_fid, e_fid) VALUES ({temp[0]}, {new_fid});")
					# 		if temp[2] == 2 or temp[2] == 3:
					# 			if ENABLE_INCLUDE:
					# 				selectdb(db, f"SELECT iid FROM bridge_include WHERE fid = {temp[0]} LIMIT 1")
					# 				iid = db[1].fetchone()
					# 				if iid is not None:
					# 					execdb(db, f"INSERT INTO bridge_include (fid, iid) VALUES ({new_fid}, {iid[0]});")
					# 			if ENABLE_CTAGS:
					# 				selectdb(db, f"SELECT tgid, lnid FROM bridge_tag WHERE fid = {temp[0]}")
					# 				tags = db[1].fetchall()
					# 				for tag in tags:
					# 					execdb(db, f"INSERT INTO bridge_tag (fid, tgid, lnid) VALUES ({new_fid}, {tag[0]}, {tag[1]});")
					# 	else:
					# 		if ENABLE_CTAGS or ENABLE_INCLUDE:
					# 			if type_c_h(cut_file[2]):
					# 				parse_include_tag(db, new_fid, new_fid, cut_file[2])
					else:
						# RENAME MODIFY
						# Get old_bf
						old_bf = m_bridge_file.get(
							m_bridge_file.vid(gp.old_vid),
							m_bridge_file.fnid( m_file_name.get( m_file_name.fname(cut_file[1]) ).fnid )
						)
						if old_bf is None:
							print("case \"R\": else: old_bf is None")
							print(cut_file[1])
							print(m_file_name.get(m_file_name.fname(cut_file[1])))
							raise _MyBreak
						# 0 New TID for old FILE
						cs.append(m_time(
							None,
							m_time.get( m_time.tid( m_file.get( m_file.fid(old_bf.fid) ).tid ) ).vid_s,
							gp.old_vid
						))
						# 1 Update old FILE
						cs.append(m_file.update(
							old_bf.fid,
							X[0].tid,
							None,
							None,
							"R"
						))

						# 2 Check if FNAME exist/Create FNAME
						cs.append(m_file_name.get_set(m_file_name.fname(cut_file[2])))
						# 3 Create FILE
						cs.append(m_file(None, gp.tid, type_check(cut_file[2]), "R", 0))
						# 4 Create BRIDGE FILE
						cs.append(m_bridge_file(gp.vid, X[2].fnid, X[3].fid))

						# 5 Create MOVED FILE
						cs.append(m_moved_file(old_bf.fid, X[3].fid))

						# INCLUDE HANDLING
						need_to_add_includes = False
						need_to_del_old_includes = False
						# Check if prior iid existed
						if old_bi := m_bridge_include.get(m_bridge_include.fid(old_bf.fid)):
							# Check if we still have one
							if includes := mf.get_includes(cut_file[1]):
								# Check if they are the same
								if mf.get_includes(cut_file[1], gp.old_version_name) == includes:
									# 6 Create BRIDGE include
									cs.append(m_bridge_include(X[2].fid, old_bi.iid))
								else:
									need_to_add_includes = True
									need_to_del_old_includes = True
							else:
								need_to_del_old_includes = True
						else:
							# Check if we have include
							if includes := mf.get_includes(cut_file[1]):
								need_to_add_includes = True

						if need_to_del_old_includes:
							# 6 New TID for old INCLUDE
							cs.append(m_time(
								None,
								m_time.get( m_time.tid( m_include.get( m_include.iid(old_bi.iid) ).tid ) ).vid_s,
								gp.old_vid
							))
							# 7 Update old INCLUDE
							cs.append(m_include.update(old_bi.iid, X[6].tid))

						if need_to_add_includes:
							# Get position of INCLUDE in cs
							pos_include = len(cs)
							# Create INCLUDE
							cs.append(m_include(None, gp.tid))
							# ? Create BRIDGE INCLUDE
							cs.append(m_bridge_include(X[2].fid, X[pos_include].iid))
							# ?? Generate include content with file names
							count_rank = 0
							for include in includes:
								cs.append(m_file_name.get_set(m_file_name.fname(include)))
								cs.append(m_include_content(X[pos_include].iid, count_rank, X[-1].fnid))
								count_rank += 1
							#EXIT INCLUDES

						# # Correct old file
						# temp = get_file(db, vid - 1, cut_file[1])
						# if temp is not None:
						# 	execdb(db, f"UPDATE file SET tid = {tid_dict.get(temp[1])}, ftype = {temp[2]}, s_stat = '{temp[3]}', e_stat = 'R' WHERE fid = {temp[0]};")
		#
						# # Create new fnid/file/bridge_file/moved_file
						# temp_fnid = fnid_dict.get(cut_file[2])
						# execdb(db, f"INSERT INTO file (tid, ftype, s_stat, e_stat) VALUES ({s_tid}, {type_check(cut_file[2])}, 'R', 0);")
						# new_fid = db[1].lastrowid
						# execdb(db, f"INSERT INTO bridge_file (vid, fnid, fid) VALUES ({vid}, {temp_fnid}, {new_fid});")
						# if temp is not None:
						# 	execdb(db, f"INSERT INTO moved_file (s_fid, e_fid) VALUES ({temp[0]}, {new_fid});")
						# if ENABLE_CTAGS or ENABLE_INCLUDE:
						# 	if type_c_h(cut_file[2]):
						# 		if temp is not None:
						# 			parse_include_tag(db, new_fid, temp[0], cut_file[2], cut_file[1])
						# 		else:
						# 			parse_include_tag(db, new_fid, new_fid, cut_file[2])
				case "M":
					# MODIFY
					# Get old_bf
					old_bf = m_bridge_file.get(
						m_bridge_file.vid(gp.old_vid),
						m_bridge_file.fnid( m_file_name.get( m_file_name.fname(cut_file[1]) ).fnid )
					)
					if old_bf is None:
						print("case \"M\": old_bf is None")
						print(cut_file[1])
						print(m_file_name.get(m_file_name.fname(cut_file[1])))
						#print(m_bridge_file.current_table)
						raise _MyBreak
					# 0 New TID for old FILE
					cs.append(m_time(
						None,
						m_time.get( m_time.tid( m_file.get( m_file.fid(old_bf.fid) ).tid ) ).vid_s,
						gp.old_vid
					))
					# 1 Update old FILE
					cs.append(m_file.update(
						old_bf.fid,
						X[0].tid,
						None,
						None,
						"M"
					))

					# 2 Create FILE
					cs.append(m_file(None, gp.tid, type_check(cut_file[1]), "M", 0))
					# 3 Create BRIDGE FILE
					cs.append(m_bridge_file(gp.vid, old_bf.fnid, X[2].fid))

					# INCLUDE HANDLING
					need_to_add_includes = False
					need_to_del_old_includes = False
					# Check if prior iid existed
					if old_bi := m_bridge_include.get(m_bridge_include.fid(old_bf.fid)):
						# Check if we still have one
						if includes := mf.get_includes(cut_file[1]):
							# Check if they are the same
							if mf.get_includes(cut_file[1], gp.old_version_name) == includes:
								# 4 Create BRIDGE include
								cs.append(m_bridge_include(X[2].fid, old_bi.iid))
							else:
								need_to_add_includes = True
								need_to_del_old_includes = True
						else:
							need_to_del_old_includes = True
					else:
						# Check if we have include
						if includes := mf.get_includes(cut_file[1]):
							need_to_add_includes = True

					if need_to_del_old_includes:
						# 4 New TID for old INCLUDE
						cs.append(m_time(
							None,
							m_time.get( m_time.tid( m_include.get( m_include.iid(old_bi.iid) ).tid ) ).vid_s,
							gp.old_vid
						))
						# 5 Update old INCLUDE
						cs.append(m_include.update(old_bi.iid, X[4].tid))

					if need_to_add_includes:
						# Get position of INCLUDE in cs
						pos_include = len(cs)
						# Create INCLUDE
						cs.append(m_include(None, gp.tid))
						# ? Create BRIDGE INCLUDE
						cs.append(m_bridge_include(X[2].fid, X[pos_include].iid))
						# ?? Generate include content with file names
						count_rank = 0
						for include in includes:
							cs.append(m_file_name.get_set(m_file_name.fname(include)))
							cs.append(m_include_content(X[pos_include].iid, count_rank, X[-1].fnid))
							count_rank += 1
					#EXIT INCLUDES
					old_tag_list = []
					if (old_tags := m_bridge_tag.get(m_bridge_tag.fid(old_bf.fid))):
						for old_tag in old_tags:
							old_tag_list.append((m_tag.get(m_tag.tgid(old_tag.tgid)), m_line.get(m_line.lnid(old_tag.lnid))))
					if (new_tags := mf.get_tags(cut_file[1])):
						for tag in new_tags:
							if not tag:
								continue
							var_moron = True
							# Is the tag in prior version, Check for name
							if (new_tag_name := m_tag_name.get(m_tag_name.tname(tag[0]))):
								# Is the tag in prior version, Check for actual tag
								for pos, old_tag in enumerate(old_tag_list):
									try:
										if old_tag[0].tnid == new_tag_name.tnid:
											new_file = mf.get_file(cut_file[1]).splitlines()
											old_file = mf.get_file(cut_file[1], gp.old_version_name).splitlines()

											if new_file[tag[1]:tag[2]] == old_file[old_tag[1].ln_s:old_tag[1].ln_e]:
												# ​(╯°□°)╯︵ ┻━┻ => (ヘ･_･)ヘ┳━┳
												# ? Create LINE
												cs.append(m_line.get_set(m_line.ln_s(tag[1]), m_line.ln_e(tag[2])))
												# ? Create BRIDGE TAG entry for old tag with new fid
												cs.append(m_bridge_tag(X[2].fid, old_tag[0].tgid, X[-1].lnid))
											else:
												# ? New TID for TAG
												cs.append(m_time(
													None,
													m_time.get( m_time.tid( m_tag.get( m_tag.tgid(old_tag[0].tgid) ).tid ) ).vid_s,
													gp.old_vid
												))
												# ? Update old TAG
												cs.append(m_tag.update(old_tag[0].tgid, X[-1].tid, None, None))
												# ? Create TAG
												cs.append(m_tag(None, gp.tid, tag[3], new_tag_name.tnid))
												# ? Create LINE
												cs.append(m_line.get_set(m_line.ln_s(tag[1]), m_line.ln_e(tag[2])))
												# ? Create BRIDGE TAG
												cs.append(m_bridge_tag(X[2].fid, X[-2].tgid, X[-1].lnid))
											var_moron = False
											del old_tag_list[pos]
											break
									except IndexError:
										continue
									except TypeError:
										print("---------------")
										print(tag)
										print("---------------")

							if var_moron:
								# ? Create TAG NAME
								cs.append(m_tag_name.get_set(m_tag_name.tname(tag[0])))
								# ? Create TAG
								cs.append(m_tag(None, gp.tid, tag[3], X[-1].tnid))
								# ? Create LINE
								cs.append(m_line.get_set(m_line.ln_s(tag[1]), m_line.ln_e(tag[2])))
								# ? Create BRIDGE TAG
								cs.append(m_bridge_tag(X[2].fid, X[-2].tgid, X[-1].lnid))
					for old_tag in old_tag_list:
						if not old_tag:
							continue
						# ? New TID for TAG
						cs.append(m_time(
							None,
							m_time.get( m_time.tid( m_tag.get( m_tag.tgid(old_tag[0].tgid) ).tid ) ).vid_s,
							gp.old_vid
						))
						# ? Update old TAG
						cs.append(m_tag.update(old_tag[0].tgid, X[-1].tid, None, None))



					# # Correct old file
					# temp = get_file(db, vid - 1, cut_file[1])
					# if temp is not None:
					# 	execdb(db, f"UPDATE file SET tid = {tid_dict.get(temp[1])}, ftype = {temp[2]}, s_stat = '{temp[3]}', e_stat = 'M' WHERE fid = {temp[0]};")
					#
					# # Create new file/bridge_file
					# temp_fnid = fnid_dict.get(cut_file[1])
					# execdb(db, f"INSERT INTO file (tid, ftype, s_stat, e_stat) VALUES ({s_tid}, {type_check(cut_file[1])}, 'M', 0);")
					# new_fid = db[1].lastrowid
					# execdb(db, f"INSERT INTO bridge_file (vid, fnid, fid) VALUES ({vid}, {temp_fnid}, {new_fid});")
					# if ENABLE_CTAGS or ENABLE_INCLUDE:
					# 	if type_c_h(cut_file[1]):
					# 		if temp is not None:
					# 			parse_include_tag(db, new_fid, temp[0], cut_file[1], cut_file[1])
					# 		else:
					# 			parse_include_tag(db, new_fid, new_fid, cut_file[1])
		except _MyBreak:
			if cs:
				print(f"This failed bad after a _MyBreak... : {cs}")
				continue

		if not cs:
			# Add or other
			# 0 Check if FNAME exist/Create FNAME
			cs.append(m_file_name.get_set(m_file_name.fname(cut_file[1])))

			# 1 Create FILE
			cs.append(m_file(None, gp.tid, type_check(cut_file[1]), "A", 0))
			# 2 Create BRIDGE FILE
			cs.append(m_bridge_file(gp.vid, X[0].fnid, X[1].fid))

			# Check for include
			if (includes := mf.get_includes(cut_file[1])):
				# 3 Create INCLUDE
				cs.append(m_include(None, gp.tid))
				# 4 Create BRIDGE INCLUDE
				cs.append(m_bridge_include(X[1].fid, X[3].iid))
				# ?? Generate include content with file names
				count_rank = 0
				for include in includes:
					cs.append(m_file_name.get_set(m_file_name.fname(include)))
					cs.append(m_include_content(X[3].iid, count_rank, X[-1].fnid))
					count_rank += 1

			if (new_tags := mf.get_tags(cut_file[1])):
				for tag in new_tags:
					if not tag:
						continue
					# ? Create TAG NAME
					cs.append(m_tag_name.get_set(m_tag_name.tname(tag[0])))
					# ? Create TAG
					cs.append(m_tag(None, gp.tid, tag[3], X[-1].tnid))
					# ? Create LINE
					cs.append(m_line.get_set(m_line.ln_s(tag[1]), m_line.ln_e(tag[2])))
					# ? Create BRIDGE TAG
					cs.append(m_bridge_tag(X[1].fid, X[-2].tgid, X[-1].lnid))


			#EXIT INCLUDES
		# Store Set
		gp.set(*cs)



				# if ENABLE_CTAGS or ENABLE_INCLUDE:
				# 	if type_c_h(cut_file[1]):
				# 		parse_include_tag(db, new_fid, new_fid, cut_file[1])
	if override_list:
		multi_proc = False
	else:
		gp.push_set_to_main()
	return


def update(version):
	print(f"=======================Working on {version}=======================")
	gp.clear_fetch_all()
	# Pre-Processing
	gp.create_new_vid(version)
	mf.add_version()
	gp.create_new_tid(gp.vid)

	gp.generate_change_list()

	## preload/dirs
	m_file_name.gen_optimized_table(m_file_name.fname())
	gp.processing_dirs()
	gp.preload_fnid()
	m_file_name.insert_set()
	m_file_name.clear_fetch()
	m_time.insert_set()
	m_time.clear_fetch()
	m_file.insert_set()
	m_file.clear_fetch()
	m_bridge_file.insert_set()
	m_bridge_file.clear_fetch()
	## preload/dirs End
	# Optimization
	m_file_name.gen_optimized_table(m_file_name.fname())
	m_tag_name.gen_optimized_table(m_tag_name.tname())
	m_line.gen_optimized_table(m_line.ln_s(), m_line.ln_e())
	m_bridge_tag.gen_optimized_table(m_bridge_tag.fid())

	m_bridge_include.gen_optimized_table(m_bridge_include.fid())

	# Main Processing
	gp.processing_changes()
	gp.processing_unchanges()

	gp.execute_all()
	#gp.print_all_set()
	gp.insert_all()
	return


def main():
	initialize_db()
	update("v3.0")
	update("v3.1")
	update("v3.2")
	update("v3.3")
	update("v3.4")
	update("v3.5")
	emergency_shutdown()
	return

if __name__ == "__main__":
	main()
