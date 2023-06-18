
from architecture.architecture_relationships import Command, Subscriber, Topic, Message
from pyros_math.graph_theory import dependecy_sort, cycle_is_present_in_any
from pyros_exceptions.pyros_exceptions import TopicCircularDependency, TopicNameCollision, SubscriberNameCollision
import time
import csv
import json

import architecture.topicLogUtil as topicLogUtil

class Scheduler:
    def __init__(self, is_sim = False, file_reading_name = None):
        self.topics = []
        self.subscribers = []
        self.is_sim = is_sim
        self.throw_exception_on_init_failure = True
        self.root_command = None
        self.writing_file_name = None
        self.file_reading_name = file_reading_name
        self.read_topics = None
        self.time_stamps = None


    def initialize(self):

        self.topics = dependecy_sort(self.topics)

        if cycle_is_present_in_any(self.topics):
            raise TopicCircularDependency("There is a circular dependency in the topics, aborting init")
        for topic in self.topics:
            print("Topic name: {}".format(topic.name))

        self.begin_log()
        self.init_hardware()
        self.check_topic_name_collision()

        if self.is_sim:
            if self.file_reading_name is None:
                raise Exception("Must provide file name to read from in simulation mode.")
            self.time_stamps, messages_contents = topicLogUtil.dump_file_contents(self.file_reading_name)
            self.read_topics = topicLogUtil.construct_dictionary_of_messages_vs_time(self.time_stamps, messages_contents)

    def advance_command(self):
        if self.root_command and self.root_command.is_complete():
            self.root_command = self.root_command.next_command

    def periodic(self):

        stored_messages = {}
        present_time = time.time()
        if self.is_sim:
            present_time = self.time_stamps.pop(0)

        if not self.root_command is None and not self.root_command.first_run_occured:
            self.root_command.first_run()
        
        self.advance_command()

        # Check if root_command is still not None after advancing
        if self.root_command is not None:
            self.root_command.periodic()
        else:
            print("No further command to execute")

        all_logged_messages = None 

        if self.is_sim:
            all_logged_messages = topicLogUtil.get_message_at_time(present_time, self.read_topics)


        for topic in self.topics:
            if self.is_sim and topic.replace_message_with_log:
                message_dictionary, current_time_seconds, delta_time_seconds = all_logged_messages[topic.name]
                message = Message(message_dictionary)
                message.time_stamp = current_time_seconds
                topic.publish_periodic_from_log(message, current_time_seconds, delta_time_seconds)
                stored_messages[topic.name] = "{0}, {1}, {2}".format(json.dumps(message.message), current_time_seconds, delta_time_seconds)
                # if we are simulating, and we are replacing the message with a log, then we need to get the message from the log
            else:
                # if not sim, or if we are not replacing the message with a log, then we need to publish the message since this implies it can be calculated with known inputs
                message, current_time_seconds, delta_time_seconds = topic.publish_periodic()
                stored_messages[topic.name] = "{0}, {1}, {2}".format(json.dumps(message.message), current_time_seconds, delta_time_seconds)
        


        # write the messages to the log file
        if not self.is_sim and stored_messages:
            with open(self.writing_file_name, 'a+') as self.f:
                self.f.write("{0}, {1}\n".format(present_time, json.dumps(stored_messages)))

        for sub in self.subscribers:
            sub.periodic()

        # often topcis are also subscribers.  All topics inherit from subscriber
        for topic in self.topics:
            topic.periodic()


    def set_command_group(self, head: Command):
        self.root_command = head

    def shutdown(self):
        pass

    # add all topics using args 
    def add_topics(self, *args):
        for topic in args:
            self.topics.append(topic)
    # add all subscribers using args
    def add_subscribers(self, *args):
        for sub in args:
            self.subscribers.append(sub)
    def begin_log(self):
        if not self.is_sim:
            self.writing_file_name = "log_" + str(int(time.time())) + ".csv"
            with open(self.writing_file_name, 'w') as self.f:
                self.f.write("Time, TopicMessageDictionaries\n")

    def init_hardware(self):
        for sub in self.subscribers:            
            success = sub.initialize_hardware()
            if self.throw_exception_on_init_failure and not success:
                raise RuntimeError("Hardware for Subscriber, '{}' failed to initialize, aborting init".format(sub.name))
            sub.is_sim = self.is_sim
    def check_topic_name_collision(self):
        visited_topics = []
        for topic in self.topics:
            for topic_other in visited_topics:
                if topic.name == topic_other.name:
                    raise RuntimeError("Two or more Topics cannot have the same name: {}, Please Check your Configuration".format(topic.name))

            visited_topics.append(topic)

            for sub in self.subscribers:
                if topic.name == sub.name:
                    raise RuntimeError("Topic and Subscriber cannot have the same name: {}".format(topic.name))