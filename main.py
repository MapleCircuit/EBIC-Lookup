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
import clang.cindex
import ctypes
import os

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


class CXSourceRangeList(ctypes.Structure):
	_fields_ = [("count", ctypes.c_uint),("ranges", ctypes.POINTER(clang.cindex.SourceRange))]

CXSourceRangeList_P = ctypes.POINTER(CXSourceRangeList)










class Ast:
	def __str__(self):
		result = f"Class: {type(self).__name__} "
		for key in vars(self):
			result += f", {key} : {getattr(self, key)} "
		return result




class CPPro_ifdef(Ast):
	def __init__(self, line_start, line_end, identifier):
		self.line_start = line_start
		self.line_end = line_end
		self.identifier = identifier

class CPPro_ifndef(Ast):
	def __init__(self, line_start, line_end, identifier):
		self.line_start = line_start
		self.line_end = line_end
		self.identifier = identifier

class CPPro_if(Ast):
	def __init__(self, line_start, line_end, expression):
		self.line_start = line_start
		self.line_end = line_end
		self.expression = expression

class CPPro_elif(Ast):
	def __init__(self, line_start, line_end, expression):
		self.line_start = line_start
		self.line_end = line_end
		self.expression = expression

class CPPro_else(Ast):
	def __init__(self, line_start, line_end):
		self.line_start = line_start
		self.line_end = line_end

class CPPro_endif(Ast):
	def __init__(self, line_start, line_end):
		self.line_start = line_start
		self.line_end = line_end

class CPPro_define(Ast):
	def __init__(self, line_start, line_end, identifier, replacement):
		self.line_start = line_start
		self.line_end = line_end
		self.identifier = identifier
		self.replacement = replacement

class CPPro_undef(Ast):
	def __init__(self, line_start, line_end, identifier):
		self.line_start = line_start
		self.line_end = line_end
		self.identifier = identifier

class CPPro_include(Ast):
	def __init__(self, line_start, line_end, written_include, actual_include):
		self.line_start = line_start
		self.line_end = line_end
		self.written_include = written_include
		self.actual_include = actual_include

class CPPro_line(Ast):
	def __init__(self, line_start, line_end, lineno, filename):
		self.line_start = line_start
		self.line_end = line_end
		self.lineno = lineno
		self.filename = filename

class CPPro_error(Ast):
	def __init__(self, line_start, line_end, error_msg):
		self.line_start = line_start
		self.line_end = line_end
		self.error_msg = error_msg

class CPPro_pragma(Ast):
	def __init__(self, line_start, line_end, pragma):
		self.line_start = line_start
		self.line_end = line_end
		self.pragma = pragma

########https://gist.github.com/ChunMinChang/88bfa5842396c1fbbc5b
def commentRemover(text):
	def replacer(match):
		s = match.group(0)
		if s.startswith('/'):
			return "\n" * s.count( "\n" )
		else:
			return s
	pattern = re.compile(
		r'//.*?$|/\*.*?\*/|\'(?:\\.|[^\\\'])*\'|"(?:\\.|[^\\"])*"',
		re.DOTALL | re.MULTILINE
	)
	return re.sub(pattern, replacer, text)
#######

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
class Change_Set:
	def __init__(self, file_name):
		self.file_name = file_name
		self.cs = []
		self.cs_processed = False
		self.cs_result = []
		self.cs_result_dict = {}
		self.includes = []
		self.tags = []
		self.tags_processed = False
	def __call__(self, *item):
		return self.cs.append(*item)

class Great_Processor:
	def __init__(self):
		global multi_proc
		multi_proc = False
		self.vid = 0
		self.loggin = []
		self.version_name = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
		self.vid = 0
		self.manager = None
		self.shared_set_list = None
		self.main_dict = {}

	def __getstate__(self):
		#useless
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
		self.shared_set_list.append(pickle.dumps(gp.main_dict))
		return

	def set(self, *args):
		self.append(args)
		return



	def execute(self):
		# doesn't include tags
		global multi_proc
		multi_proc = False
		for CS in self.main_dict.values():
			x = []
			for item in CS.cs:
				while item.__class__.__name__ == "Delayed_Executor":
					item = item.process(CS.cs_result)
				CS.cs_result.append(item)

				if not CS.cs_result_dict.get(item.__class__.__name__):
					CS.cs_result_dict[item.__class__.__name__] = []
				CS.cs_result_dict[item.__class__.__name__].append(item)

			CS.cs_processed = True
			#print(f"execute() results:{x}")
		return

	def execute_all(self):
		print("Great_Processor.execute() start")
		if len(self.shared_set_list) != CPUS-1:
			print(f"You have {len(self.shared_set_list)} set_list. We need {CPUS-1}!!! Exiting now!")
			emergency_shutdown()
		for remote_gp in self.shared_set_list:
			self.main_dict.update(pickle.loads(remote_gp))
		self.execute()

		#self.handling_tags()
		self.main_dict = {}
		print("Great_Processor.execute_all() done")
		return

	def get_on_fname(self, fname, table, only_first=True):
		# Will return the table entry(ies) given a fname and table. Will look in currently processed CS and, if not found, search db for prior version
		#####NEEDS TO BE FIXED AS IT MAY RETURN MORE THAN EXPECTED AS WE DO GET_SET ON RANDOM THINGS..... (FOR THE MAIN_DICT PART...)
		if self.main_dict.get(fname):
			if (result := self.main_dict[fname].cs_result_dict.get(table)):
				if only_first:
					return result[0]
				else:
					return result

		if not (fn := m_file_name.get(m_file_name.fname(fname))):
			return None
		if table == "m_file_name":
			return fn


		if not (mbf := m_bridge_file.get(m_bridge_file.vid(self.old_vid), m_bridge_file.fnid(fn.fnid))):
			return None
		if table == "m_bridge_file":
			return mbf

		if table == "m_file":
			return m_file.get(m_file.fid(mbf.fid))

		## THIS ASSUMES THE ONLY THING WE COULD WANT AT THIS POINT IS INCLUDES
		if not (mbi := m_bridge_include.get(m_bridge_include.fid(mbf.fid))):
			return None
		if table == "m_bridge_include":
			return mbi

		if table == "m_include":
			return m_include.get(m_include.iid(mbi.iid))
		if table == "m_include_content":
			mic = m_include_content.get(m_include_content.iid(mbi.iid))
			if mic is None:
				return None
			if only_first:
				return mic[0]
			return mic

		# i don't know what you want!
		print(f"get_on_fname is not built for this! Returning None! Fname: {fname} Table: {table}")
		return None



	def handling_tags(self):

		while len(gp.main_dict) != 0:
			print("goat dead")





		return


	def insert_all(self):
		for table in self.loggin:
			table.insert_set()
			table.insert_update()
		return

	def drop_all(self):
		sql_drop = "DROP TABLE "
		db = set_db()
		execdb(db, "SET FOREIGN_KEY_CHECKS = 0;")
		for table in self.loggin:
				sql_drop += f"`{table.table_name}`, "
		print(sql_drop[:-2])
		for x in range(3):
			try:
				execdb(db, sql_drop[:-2])
			except Exception as e:
				print("drop failed")
		unset_db(db)
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
	def __init__(self, table_name: str, columns: tuple, primary: tuple, foreign=None, initial_insert=None, no_duplicate=False, get_list=False):
		self.table_name = table_name
		self.init_columns = columns
		self.init_primary = primary
		self.init_foreign = foreign
		self.initial_insert = initial_insert
		self.no_duplicate = no_duplicate
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
			self.no_duplicate_dict = {}
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
			if self.no_duplicate:
				if (no_dup_key := self.no_duplicate_dict.get(item[1:])) is not None:
					return self.set_table[no_dup_key]

				while self.set_index in self.set_table:
					self.set_index += 1

				item = (self.set_index,) + item[1:]
				self.no_duplicate_dict[item[1:]] = self.set_index
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

m_include_content = Table("m_include_content", (("iid", "INT", "NOT NULL"),("rank", "INT", "NOT NULL"),("fnid", "INT", "NOT NULL")), ("iid","rank"), (("iid", "m_include", "iid"),("fnid","m_file_name","fnid")), None , False, True)

m_bridge_include = Table("m_bridge_include", (("fid", "INT", "NOT NULL"),("iid", "INT", "NOT NULL")), ("fid","iid"), (("fid","m_file","fid"),("iid", "m_include", "iid")), None)

m_tag_name = Table("m_tag_name", (("tnid", "INT", "NOT NULL", "AUTO_INCREMENT"),("tname", "VARCHAR(255)", "NOT NULL", "COLLATE utf8mb4_bin")), ("tnid",), None, ((0,""),), True)

m_ast = Table("m_ast", (("aid", "INT", "NOT NULL", "AUTO_INCREMENT"),("tnid", "INT", "NOT NULL"),("tinfo", "TINYINT", "UNSIGNED", "NOT NULL")), ("aid",), (("tnid","m_tag_name","tnid"),), ((0,0,0),))

# Think about unions and kconfig
# encode typedefs HERE
m_ast_struct = Table("m_ast_struct", (("aid", "INT", "NOT NULL"),("rank", "INT", "NOT NULL"),("tnid", "INT", "NOT NULL"),("inneraid", "INT", "NOT NULL"),("tspec", "INT", "NOT NULL")), ("aid","rank"), (("tnid","m_tag_name","tnid"),("aid","m_ast","aid"),("inneraid","m_ast","aid")), None, False, True)

# TypeKind use values from TypeKind in cindex to store along with the name so that you can know wtf it is
m_ast_type = Table("m_ast_type", (("aid", "INT", "NOT NULL"),("tnid", "INT", "NOT NULL"),("typekind", "INT", "NOT NULL")), ("aid",), (("aid","m_ast","aid"),("tnid","m_tag_name","tnid")))

m_tag = Table("m_tag", (("tgid", "INT", "NOT NULL", "AUTO_INCREMENT"),("tid", "INT", "NOT NULL"),("ttype", "TINYINT", "UNSIGNED", "NOT NULL"),("tnid", "INT", "NOT NULL"),("tspec", "INT", "NOT NULL"),("aid", "INT")), ("tgid",), (("tid","m_time","tid"),("tnid","m_tag_name","tnid"),("aid","m_ast","aid")), ((0,0,0,0,0,0),))

#m_tag_content = Table("m_tag_content", (("tgid", "INT", "NOT NULL"),("rank", "INT", "NOT NULL"),("mtgid", "INT", "NOT NULL")), ("tgid","rank"), (("tgid","m_tag","tgid"),("mtgid","m_tag","tgid")), None, False, True)

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

	print("Creating m_type")
	m_ast.create_table()

	print("Creating m_type_struct")
	m_ast_struct.create_table()

	print("Creating m_type_type")
	m_ast_type.create_table()

	print("Creating m_tag")
	m_tag.create_table()

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
# Maple's weirdest friend, Ned the Fox
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
				#include 			 <my_aids.h­­>
					match item[9]:
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


	#def ast_type_sniffer(self, cursor):
#type.get_canonical()

	def ast_struct_sniffer(self, cursor):
		saved_extent = None
		sub_processing_list = []
		for kids in cursor.get_children():
			print(f"-----{kids.spelling}-----{kids.kind}")
			kind = f"{kids.kind}"

			if kind == "CursorKind.STRUCT_DECL":
				sub_processing_list.append(["CursorKind.STRUCT_DECL", f"{kids.spelling}", kids.extent.start.line, kids.extent.start.column, kids.extent.end.line, kids.extent.end.column])
				saved_extent = kids.spelling
				print("-")


				###### SHIT
				if kids.type.get_pointee():
					print(f"{kids.type.get_pointee().get_declaration().get_definition()}")
				else:
					print("we None in kids.type.get_declaration()")
				######/ SHIT

			elif kind == "CursorKind.FIELD_DECL":
				if f"{saved_extent}" == f"{kids.type.get_pointee().get_declaration().spelling}":
					sub_processing_list[-1].append(["CursorKind.FIELD_DECL", f"{kids.spelling}"])
					print("hi, i should be in the prior struct")
				else:
					saved_extent = None
					sub_processing_list.append(["CursorKind.FIELD_DECL", f"{kids.spelling}", kids.extent.start.line, kids.extent.start.column, kids.extent.end.line, kids.extent.end.column])
				print(f"typedef-type")

			else:
				print("War crime")

		return sub_processing_list

# 1. scan ifdefs, endif, if(latreretgfuhdfb ) ifndef
# 2. STRCUT
# 3. FUNCTION

	def preproparse(self, current_file, current_line, file_path):
		working_line = current_file[current_line].lstrip()

		loopval = 0
		if working_line == "":
			return
		if working_line[0] != '#':
			return

		try:
			working_line = working_line[0] + working_line[1:].lstrip()
		except IndexError:
			return


		while current_file[current_line+loopval][-1] == "\\":

			try:
				current_file[current_line+loopval+1]
			except IndexError:
				break

			loopval += 1
			if (current_file[current_line+loopval][0] == " ") or (current_file[current_line+loopval][0] == "\t"):
				working_line = working_line[:-1] + " \n" + current_file[current_line+loopval].lstrip()
			else:
				working_line = working_line[:-1] + "\n" + current_file[current_line+loopval]


		if working_line.startswith("#ifdef"):
			return CPPro_ifdef(current_line+1, current_line+1+loopval, working_line[6:].lstrip())

		if working_line.startswith("#ifndef"):
			return CPPro_ifndef(current_line+1, current_line+1+loopval, working_line[7:].lstrip())

		if working_line.startswith("#if"):
			return CPPro_if(current_line+1, current_line+1+loopval, working_line[3:].lstrip())

		if working_line.startswith("#elifndef"):
			print (f"SOME RETARDED DEVS, ADDED THIS FUCKING BULSHIT TO THEIR CODE: #elifndef , Line:{current_line+1}")
			emergency_shutdown()
		if working_line.startswith("#elifdef"):
			print (f"SOME RETARDED DEVS, ADDED THIS FUCKING BULSHIT TO THEIR CODE: #elifdef , Line:{current_line+1}")
			emergency_shutdown()

		if working_line.startswith("#elif"):
			return CPPro_elif(current_line+1, current_line+1+loopval, working_line[5:].lstrip())

		if working_line.startswith("#else"):
			return CPPro_else(current_line+1, current_line+1+loopval)

		if working_line.startswith("#endif"):
			return CPPro_endif(current_line+1, current_line+1+loopval)

		if working_line.startswith("#define"):
			working_line = working_line[7:].lstrip()
			parentheses = 0
			bypass = False
			arg_one = ""
			arg_two = ""
			for line_char in working_line:
				if not bypass:
					if line_char == "\n":
						continue
					if line_char == '(':
						parentheses += 1
					elif (line_char == ' ') or (line_char == '\t'):
						if parentheses == 0:
							bypass = True
					elif line_char == ')':
						parentheses -= 1
						if parentheses == 0:
							bypass = True

				if bypass:
					arg_two += line_char
				else:
					arg_one += line_char


			arg_two = arg_two.lstrip()
			if arg_two == "":
				arg_two = None

			return CPPro_define(current_line+1, current_line+1+loopval, arg_one, arg_two)

		if working_line.startswith("#undef"):
			return CPPro_undef(current_line+1, current_line+1+loopval, working_line[6:].lstrip())



		if working_line.startswith("#include"):
			working_line = working_line[8:].lstrip()
			if working_line == "":
				return CPPro_include(current_line+1, current_line+1+loopval, "", "")

			if working_line[0] == "\"":
				written_include = "\""
				actual_path = f"{Path(file_path).parent}/"
				for line_char in working_line[1:]:
					written_include += line_char
					if line_char == "\"":
						break
			elif working_line[0] == "<":
				written_include = "<"
				actual_path = "include/"
				for line_char in working_line[1:]:
					written_include += line_char
					if line_char == ">":
						break
			else:
				return CPPro_include(current_line+1, current_line+1+loopval, "", "")


			# PARSE THE ACTUAL INCLUDE
			written_include[1:-2]

			path_arr = []
			dotdot = 0
			# IT WILL FUCKING BREAK IF SOME RETARD PUT SOME ROOT PATH IN THERE LIBS, WHY WOULD SOMEONE DO SOMETHING SO WRONG???? WHO THE FUCJK KNOWS!!!! BEWARE
			for chunk in str(actual_path + written_include[1:-1]).split("/")[::-1]:
				if chunk == "..":
					dotdot += 1
				elif dotdot > 0:
					dotdot -= 1
				else:
					path_arr.append(chunk)


			return CPPro_include(current_line+1, current_line+1+loopval, written_include, "/".join(path_arr[::-1]))


		if working_line.startswith("#line"):
			line_in_work = working_line[5:].lstrip()

			lineno = re.match(r'^\d+', line_in_work)

			try:
				filename = line_in_work[len(lineno):].lstrip()
			except IndexError:
				filename = None

			return CPPro_line(current_line+1, current_line+1+loopval, int(lineno), filename)


		if working_line.startswith("#error"):
			return CPPro_error(current_line+1, current_line+1+loopval, working_line[6:].lstrip().rstrip())

		if working_line.startswith("#pragma"):
			return CPPro_pragma(current_line+1, current_line+1+loopval, working_line[7:].lstrip())


		return



	def pre_parse(self, current_file, file_path):

		# Cleanup
		current_file = commentRemover(current_file).splitlines()

		#fucjk = tuple(map(lambda x: self.preproparse(current_file, x[0], file_path), enumerate(current_file)))

		bypass_num = 0
		for shit in range(len(current_file)):
			if shit<bypass_num:
				continue
			result = self.preproparse(current_file, shit, file_path)
			if result:
				if (temp := getattr(result, "line_end")) is not None:
					bypass_num = temp
				print(result)

		emergency_shutdown()

		# ifdef only contains 1 thing at a time so they are stored in the db using type
		p_ifdef = tuple(map(lambda y: y[6:].lstrip(), filter(lambda x: x.lstrip().startswith("#ifdef"), current_file)))

		p_ifndef = tuple(map(lambda y: y[7:].lstrip(), filter(lambda x: x.lstrip().startswith("#ifndef"), current_file)))
		#THIS DOPESNT FUCKING WORK ASFDBJGYDTCYHSBG DFHS
		p_if = tuple(map(lambda y: y[3:].lstrip(), filter(lambda x: (x.lstrip().startswith("#if") and not x.lstrip().startswith("#ifndef")), current_file)))
		p_else = tuple(map(lambda y: y[5:].lstrip(), filter(lambda x: x.lstrip().startswith("#else"), current_file)))
		p_elsif = tuple(map(lambda y: y[6:].lstrip(), filter(lambda x: x.lstrip().startswith("#elsif"), current_file)))
		p_endif = tuple(map(lambda y: y[6:].lstrip(), filter(lambda x: x.lstrip().startswith("#endif"), current_file)))

		print(f"p_ifdef={p_ifdef}")
		print(f"p_ifndef={p_ifndef}")
		print(f"p_if={p_if}")
		print(f"p_else={p_else}")
		print(f"p_elsif={p_elsif}")
		print(f"p_endif={p_endif}")
		return p_ifdef

	# include/linux/lockd/bind.h
	def ast_type(self, file_path, version=None):
		if version is None:
			version=gp.version_name

		current_file = self.get_file(file_path, version)
		pre_parse_r = self.pre_parse(current_file, file_path)

		# Initialize the Clang index
		index = clang.cindex.Index.create()

		translation_unit = index.parse(f"{mf.version_dict[version]}/{file_path}", args=[
			"-D__KERNEL__",#"-nostdinc",
			f"-I{mf.version_dict[version]}/{"/".join(file_path.split("/")[:-1])}",
			f"-I{mf.version_dict[version]}/include",
			f"-I{mf.version_dict[version]}/include/uapi"
		],
		options=clang.cindex.TranslationUnit.PARSE_DETAILED_PROCESSING_RECORD)

		###########################################################################
		clang.cindex.conf.lib.clang_getSkippedRanges.restype = CXSourceRangeList_P#
		###########################################################################
		Skipped_ranges = clang.cindex.conf.lib.clang_getSkippedRanges(
			translation_unit,
			translation_unit.get_file(f"{mf.version_dict[version]}/{file_path}")
		)


		print("----")
		for i in range(Skipped_ranges.contents.count):
			print(Skipped_ranges.contents.ranges[i])
			if current_file[Skipped_ranges.contents.ranges[i].start.line-1].startswith("#ifdef"):
				for FUCJK in current_file[Skipped_ranges.contents.ranges[i].start.line-1].split(" ")[1:]:
					print(FUCJK)
			for x in current_file[Skipped_ranges.contents.ranges[i].start.line-1:Skipped_ranges.contents.ranges[i].end.line]:
				print(x)


		for include in translation_unit.get_includes():
			print(include.source)


		# PROCESS LOOP
		processing_list = []
		for kids in translation_unit.cursor.get_children():
			if f"{kids.location.file}" == f"{mf.version_dict[version]}/{file_path}":
				print(f"{kids.spelling}-----{kids.kind}")
				if f"{kids.kind}" == "CursorKind.STRUCT_DECL":
					processing_list.append([f"{kids.spelling}", kids.extent.start.line, kids.extent.start.column, kids.extent.end.line, kids.extent.end.column, self.ast_struct_sniffer(kids)])

		print("----------")
		# PRINT LOOP
		for x in processing_list:
			print(x[:5])
			for y in x[5]:
				print("   " + str(y))

		print("----------")
		# DEBUG LOOP
		if translation_unit.diagnostics:
			print("Generic Parse Errors:")
			for diag in translation_unit.diagnostics:
				print(f"  - {diag.spelling} (Line:{diag.location.line} File:{diag.location.file})")
		return


	def ast_nightmare(self, file_path, version=None):
		if version is None:
			version=gp.version_name
		# Initialize the Clang index
		index = clang.cindex.Index.create()

		# Parse the source file
		translation_unit = index.parse(f"{mf.version_dict[version]}/{file_path}")
		for kids in translation_unit.cursor.get_children():
			processing_list = []
			if f"{kids.location.file}" == f"{mf.version_dict[version]}/{file_path}":
				if f"{kids.kind}" == "CursorKind.FUNCTION_DECL":
					processing_list.append(1)
					processing_list.append(kids.spelling)
					processing_list.append(kids.extent.start.line)
					processing_list.append(kids.extent.start.column)
					processing_list.append(kids.extent.end.line)
					processing_list.append(kids.extent.end.column)

					for todlers in kids.get_arguments():
						if f"{todlers.location.file}" == f"{mf.version_dict[version]}/{file_path}":
							processing_list.append([2])
							processing_list[-1].append(todlers.spelling)
							bitmap = 0
							bitmap_p = 0

							if todlers.is_const_method():
								bitmap += 1 << 0
							if todlers.is_static_method():
								bitmap += 1 << 1
							if f"{todlers.type.kind}" == "TypeKind.POINTER":
								bitmap_p += 1 << 0
								if todlers.type.get_pointee().is_const_qualified():
									bitmap_p += 1 << 1
							processing_list[-1].append(bitmap)
							processing_list[-1].append(bitmap_p)
							processing_list[-1].append(todlers.type.kind)
					print(processing_list)


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
	command = [
		"ln",
		"-s",
		"asm-generic",
		f"{temp_path}/include/asm"
	]
	sp.run(command)
	command = [
		"ln",
		"-s",
		"asm-generic",
		f"{temp_path}/include/uapi/asm"
	]
	sp.run(command)
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
		CS = None
		try:
			match cut_file[0][0]:
				case "D":
					# DELETE
					CS = Change_Set(cut_file[1])
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
					CS(m_time(
						None,
						m_time.get( m_time.tid( m_file.get( m_file.fid(old_bf.fid) ).tid ) ).vid_s,
						gp.old_vid
					))
					# 1 Update FILE
					CS(m_file.update(
						old_bf.fid,
						X[0].tid,
						None,
						None,
						"D"
					))

					# Check if iid existed
					if (temp_iid := m_bridge_include.get(m_bridge_include.fid(old_bf.fid))):
						# 2 New TID for INCLUDE
						CS(m_time(
							None,
							m_time.get( m_time.tid( m_include.get( m_include.iid(temp_iid.iid) ).tid ) ).vid_s,
							gp.old_vid
						))
						# 3 Update INCLUDE
						CS(m_include.update(temp_iid.iid, X[2].tid))
					#EXIT INCLUDES

				case "R":
					CS = Change_Set(cut_file[2])

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
						CS(m_time(
							None,
							m_time.get( m_time.tid( m_file.get( m_file.fid(old_bf.fid) ).tid ) ).vid_s,
							gp.old_vid
						))
						# 1 Update old FILE
						CS(m_file.update(
							old_bf.fid,
							X[0].tid,
							None,
							None,
							"R"
						))

						# 2 Check if FNAME exist/Create FNAME
						CS(m_file_name.get_set(m_file_name.fname(cut_file[2])))
						# 3 Create FILE
						CS(m_file(None, gp.tid, type_check(cut_file[2]), "R", 0))
						# 4 Create BRIDGE FILE
						CS(m_bridge_file(gp.vid, X[2].fnid, X[3].fid))

						# 5 Create MOVED FILE
						CS(m_moved_file(old_bf.fid, X[3].fid))

						# Check if iid existed
						if (temp_iid := m_bridge_include.get(m_bridge_include.fid(old_bf.fid))):
							# 6 Create BRIDGE INCLUDE
							CS(m_bridge_include(X[3].fid, temp_iid.iid))
						#EXIT INCLUDES

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
						CS(m_time(
							None,
							m_time.get( m_time.tid( m_file.get( m_file.fid(old_bf.fid) ).tid ) ).vid_s,
							gp.old_vid
						))
						# 1 Update old FILE
						CS(m_file.update(
							old_bf.fid,
							X[0].tid,
							None,
							None,
							"R"
						))

						# 2 Check if FNAME exist/Create FNAME
						CS(m_file_name.get_set(m_file_name.fname(cut_file[2])))
						# 3 Create FILE
						CS(m_file(None, gp.tid, type_check(cut_file[2]), "R", 0))
						# 4 Create BRIDGE FILE
						CS(m_bridge_file(gp.vid, X[2].fnid, X[3].fid))

						# 5 Create MOVED FILE
						CS(m_moved_file(old_bf.fid, X[3].fid))

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
									CS(m_bridge_include(X[2].fid, old_bi.iid))
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
							CS(m_time(
								None,
								m_time.get( m_time.tid( m_include.get( m_include.iid(old_bi.iid) ).tid ) ).vid_s,
								gp.old_vid
							))
							# 7 Update old INCLUDE
							CS(m_include.update(old_bi.iid, X[6].tid))

						if need_to_add_includes:
							# Get position of INCLUDE in cs
							pos_include = len(CS.cs)
							# Create INCLUDE
							CS(m_include(None, gp.tid))
							# ? Create BRIDGE INCLUDE
							CS(m_bridge_include(X[2].fid, X[pos_include].iid))
							# ?? Generate include content with file names
							count_rank = 0
							for include in includes:
								CS(m_file_name.get_set(m_file_name.fname(include)))
								CS(m_include_content(X[pos_include].iid, count_rank, X[-1].fnid))
								count_rank += 1
							#EXIT INCLUDES

				case "M":
					# MODIFY
					CS = Change_Set(cut_file[1])
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
					CS(m_time(
						None,
						m_time.get( m_time.tid( m_file.get( m_file.fid(old_bf.fid) ).tid ) ).vid_s,
						gp.old_vid
					))
					# 1 Update old FILE
					CS(m_file.update(
						old_bf.fid,
						X[0].tid,
						None,
						None,
						"M"
					))

					# 2 Create FILE
					CS(m_file(None, gp.tid, type_check(cut_file[1]), "M", 0))
					# 3 Create BRIDGE FILE
					CS(m_bridge_file(gp.vid, old_bf.fnid, X[2].fid))

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
								CS(m_bridge_include(X[2].fid, old_bi.iid))
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
						CS(m_time(
							None,
							m_time.get( m_time.tid( m_include.get( m_include.iid(old_bi.iid) ).tid ) ).vid_s,
							gp.old_vid
						))
						# 5 Update old INCLUDE
						CS(m_include.update(old_bi.iid, X[4].tid))

					if need_to_add_includes:
						# Get position of INCLUDE in cs
						pos_include = len(CS.cs)
						# Create INCLUDE
						CS(m_include(None, gp.tid))
						# ? Create BRIDGE INCLUDE
						CS(m_bridge_include(X[2].fid, X[pos_include].iid))
						# ?? Generate include content with file names
						count_rank = 0
						for include in includes:
							CS(m_file_name.get_set(m_file_name.fname(include)))
							CS(m_include_content(X[pos_include].iid, count_rank, X[-1].fnid))
							count_rank += 1
					#EXIT INCLUDES

		except _MyBreak:
			if CS:
				print(f"This failed bad after a _MyBreak... : {CS}")
				continue

		if not CS:
			# Add or other
			CS = Change_Set(cut_file[1])
			# 0 Check if FNAME exist/Create FNAME
			CS(m_file_name.get_set(m_file_name.fname(cut_file[1])))

			# 1 Create FILE
			CS(m_file(None, gp.tid, type_check(cut_file[1]), "A", 0))
			# 2 Create BRIDGE FILE
			CS(m_bridge_file(gp.vid, X[0].fnid, X[1].fid))
			# Check for include
			if (includes := mf.get_includes(cut_file[1])):
				CS.includes.append(includes)
				# 3 Create INCLUDE
				CS(m_include(None, gp.tid))
				# 4 Create BRIDGE INCLUDE
				CS(m_bridge_include(X[1].fid, X[3].iid))
				# ?? Generate include content with file names
				count_rank = 0
				for include in includes:
					CS(m_file_name.get_set(m_file_name.fname(include)))
					CS(m_include_content(X[3].iid, count_rank, X[-1].fnid))
					count_rank += 1

			#EXIT INCLUDES

		# Store Set
		gp.main_dict[CS.file_name] = CS

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
	#include/linux/netfilter_bridge/ebtables.h
	mf.ast_type("security/capability.c")
	#mf.ast_nightmare("tools/usb/ffs-test.c")
	emergency_shutdown()


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
	gp.drop_all()
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
