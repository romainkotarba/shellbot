#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
import os
import mock
from multiprocessing import Manager, Process, Queue
import sys
import time

from shellbot import Context, Engine, ShellBot, MachinesFactory
from shellbot.spaces import Space, LocalSpace, SparkSpace


class FakeBot(object):
    def __init__(self, engine=None, space_id=None):
        self.engine = engine
        self.space_id = space_id if space_id else '*bot'
        self.store = self.engine.build_store(space_id)


class MyCounter(object):
    def __init__(self, name='counter'):
        self.name = name
        self.count = 0
    def on_bond(self):
        logging.info('{}.on_bond'.format(self.name))
        self.count += 1
    def on_dispose(self):
        logging.info('{}.on_dispose'.format(self.name))
        self.count += 1
    def __del__(self):
        logging.info('(Deleting {})'.format(self.name))


class EngineTests(unittest.TestCase):

    def setUp(self):
        self.context = Context()
        self.engine = Engine(context=self.context,
                             mouth=Queue())
        self.space = LocalSpace(context=self.context)
        self.engine.space = self.space


    def tearDown(self):
        del self.space
        del self.engine
        del self.context
        collected = gc.collect()
        if collected:
            logging.info("Garbage collector: collected %d objects." % (collected))

    def test_init(self):

        logging.info('*** init ***')

        engine = Engine(context=self.context)

        self.assertEqual(engine.context, self.context)
        self.assertTrue(engine.mouth is None)
        self.assertTrue(engine.speaker is not None)
        self.assertTrue(engine.ears is None)
        self.assertTrue(engine.listener is not None)
        self.assertFalse(engine.space is None)
        self.assertTrue(engine.server is None)
        self.assertTrue(engine.shell is not None)
        self.assertTrue(engine.subscribed is not None)
        self.assertEqual(engine.bots, {})
        self.assertEqual(engine.driver, ShellBot)
        self.assertEqual(engine.machine_factory, None)

        del engine

        engine = Engine(context=self.context,
                        type='local',
                        mouth='m',
                        ears='e')

        self.assertEqual(engine.context, self.context)
        self.assertEqual(engine.mouth, 'm')
        self.assertTrue(engine.speaker is not None)
        self.assertEqual(engine.ears, 'e')
        self.assertTrue(engine.listener is not None)
        self.assertTrue(engine.space is not None)
        self.assertTrue(engine.server is None)
        self.assertTrue(engine.shell is not None)
        self.assertTrue(engine.subscribed is not None)
        self.assertEqual(engine.bots, {})
        self.assertEqual(engine.driver, ShellBot)
        self.assertEqual(engine.machine_factory, None)

        del engine

        engine = Engine(context=self.context,
                        space=self.space,
                        mouth='m',
                        ears='e')

        self.assertEqual(engine.context, self.context)
        self.assertEqual(engine.mouth, 'm')
        self.assertTrue(engine.speaker is not None)
        self.assertEqual(engine.ears, 'e')
        self.assertTrue(engine.listener is not None)
        self.assertEqual(engine.space, self.space)
        self.assertTrue(engine.server is None)
        self.assertTrue(engine.shell is not None)
        self.assertTrue(engine.subscribed is not None)
        self.assertEqual(engine.bots, {})
        self.assertEqual(engine.driver, ShellBot)
        self.assertEqual(engine.machine_factory, None)

        del engine

        engine = Engine(context=self.context,
                        driver=FakeBot,
                        machine_factory=MachinesFactory)

        self.assertEqual(engine.context, self.context)
        self.assertEqual(engine.mouth, None)
        self.assertTrue(engine.speaker is not None)
        self.assertEqual(engine.ears, None)
        self.assertTrue(engine.listener is not None)
        self.assertTrue(engine.space is not None)
        self.assertTrue(engine.server is None)
        self.assertTrue(engine.shell is not None)
        self.assertTrue(engine.subscribed is not None)
        self.assertEqual(engine.bots, {})
        self.assertEqual(engine.driver, FakeBot)
        self.assertEqual(engine.machine_factory, MachinesFactory)

        self.context.apply({
            'bot': {'name': 'testy', 'version': '17.4.1'},
            })
        engine = Engine(context=self.context)
        self.assertEqual(engine.name, 'testy')
        self.assertEqual(engine.version, '17.4.1')

        del engine

    def test_configure(self):

        logging.info('*** configure ***')

        self.engine.configure({})

        self.engine.context.clear()
        settings = {

            'bot': {
                'on_enter': 'Hello!',
                'on_exit': 'Bye!',
            },

            'local': {
                'title': 'space name',
                'moderators': ['foo.bar@acme.com'],
                'participants': ['joe.bar@acme.com'],
            },

            'server': {
                'url': 'http://to.no.where',
                'hook': '/hook',
                'binding': '0.0.0.0',
                'port': 8080,
            },

        }
        self.engine.configure(settings)
        self.assertEqual(self.engine.get('bot.on_enter'), 'Hello!')
        self.assertEqual(self.engine.get('bot.on_exit'), 'Bye!')
        self.assertEqual(self.engine.get('local.title'), 'space name')
        self.assertEqual(self.engine.get('local.moderators'),
                         ['foo.bar@acme.com'])
        self.assertEqual(self.engine.get('local.participants'),
                         ['joe.bar@acme.com'])
        self.assertEqual(self.engine.get('server.url'), 'http://to.no.where')
        self.assertEqual(self.engine.get('server.hook'), '/hook')

        self.engine.context.clear()
        self.engine.configure_from_path(os.path.dirname(os.path.abspath(__file__))
                                      + '/test_settings/regular.yaml')
        self.assertEqual(self.engine.get('bot.on_enter'), 'How can I help you?')
        self.assertEqual(self.engine.get('bot.on_exit'), 'Bye for now')
        self.assertEqual(self.engine.get('local.title'), 'Support room')
        self.assertEqual(self.engine.get('local.moderators'),
                         ['foo.bar@acme.com'])
        self.assertEqual(self.engine.get('local.participants'),
                         ['joe.bar@acme.com', 'super.support@help.org'])
        self.assertEqual(self.engine.get('server.url'), None)
        self.assertEqual(self.engine.get('server.hook'), None)
        self.assertEqual(self.engine.get('server.binding'), None)
        self.assertEqual(self.engine.get('server.port'), None)

    def test_configuration_2(self):

        logging.info('*** configure 2 ***')

        settings = {

            'bot': {
                'on_enter': 'Hello!',
                'on_exit': 'Bye!',
            },

            'local': {
                'title': 'Support room',
                'moderators': ['foo.bar@acme.com'],
            },

            'server': {
                'url': 'http://to.nowhere/',
                'trigger': '/trigger',
                'hook': '/hook',
                'binding': '0.0.0.0',
                'port': 8080,
            },

        }

        context = Context(settings)
        engine = Engine(context=context, configure=True)
        self.assertEqual(engine.get('bot.on_enter'), 'Hello!')
        self.assertEqual(engine.get('bot.on_exit'), 'Bye!')
        self.assertEqual(engine.get('local.title'), 'Support room')
        self.assertEqual(engine.get('local.moderators'),
                         ['foo.bar@acme.com'])
        self.assertEqual(engine.get('local.participants'), [])
        self.assertEqual(engine.get('server.url'), 'http://to.nowhere/')
        self.assertEqual(engine.get('server.hook'), '/hook')
        self.assertEqual(engine.get('server.trigger'), '/trigger')
        self.assertEqual(engine.get('server.binding'), None)
        self.assertEqual(engine.get('server.port'), 8080)

    def test_configure_default(self):

        logging.info('*** configure/default configuration ***')

        logging.debug("- default configuration is not interpreted")

        os.environ["BOT_ON_ENTER"] = 'Hello!'
        os.environ["BOT_ON_EXIT"] = 'Bye!'
        os.environ["CHAT_ROOM_TITLE"] = 'Support room'
        os.environ["CHAT_ROOM_MODERATORS"] = 'foo.bar@acme.com'
        os.environ["CISCO_SPARK_BOT_TOKEN"] = '*token'
        os.environ["SERVER_URL"] = 'http://to.nowhere/'
        self.engine.configure()

        self.assertEqual(self.engine.get('bot.on_enter'), 'Hello!')
        self.assertEqual(self.engine.get('bot.on_exit'), 'Bye!')

        self.assertEqual(self.engine.get('local.title'), 'Support room')
        self.assertEqual(self.engine.get('local.moderators'), 'foo.bar@acme.com')
        self.assertEqual(self.engine.get('local.participants'), [])
        self.assertEqual(self.engine.get('local.token'), None)

        self.assertEqual(self.engine.get('server.url'), '$SERVER_URL')
        self.assertEqual(self.engine.get('server.hook'), '/hook')
        self.assertEqual(self.engine.get('server.binding'), None)
        self.assertEqual(self.engine.get('server.port'), 8080)

#        self.engine.context.clear()
#        os.environ['CHAT_ROOM_TITLE'] = 'Notifications'
#        engine = Engine(context=self.context, settings=None, configure=True)
#        self.assertEqual(engine.get('spark.room'), 'Notifications')

    def test_get(self):

        logging.info('*** get ***')

        os.environ["BOT_ON_ENTER"] = 'Hello!'
        os.environ["BOT_ON_EXIT"] = 'Bye!'
        os.environ["CHAT_ROOM_TITLE"] = 'Support room'
        os.environ["CHAT_ROOM_MODERATORS"] = 'foo.bar@acme.com'
        os.environ["CISCO_SPARK_BOT_TOKEN"] = '*token'
        os.environ["SERVER_URL"] = 'http://to.nowhere/'

        settings = {

            'bot': {
                'on_enter': 'Hello!',
                'on_exit': 'Bye!',
            },

            'local': {
                'title': '$CHAT_ROOM_TITLE',
                'moderators': '$CHAT_ROOM_MODERATORS',
            },

            'server': {
                'url': '$SERVER_URL',
                'hook': '/hook',
                'binding': '0.0.0.0',
                'port': 8080,
            },

        }

        self.engine.configure(settings=settings)

        self.assertEqual(self.engine.get('bot.on_enter'), 'Hello!')
        self.assertEqual(self.engine.get('bot.on_exit'), 'Bye!')
        self.assertEqual(self.engine.get('local.title'), 'Support room')
        self.assertEqual(self.engine.get('local.moderators'),
                         'foo.bar@acme.com')
        self.assertEqual(self.engine.get('local.participants'), [])

        self.assertEqual(self.engine.get('local.token'), None)

        self.assertEqual(self.engine.get('server.url'), 'http://to.nowhere/')
        self.assertEqual(self.engine.get('server.hook'), '/hook')
        self.assertEqual(self.engine.get('server.binding'), None)
        self.assertEqual(self.engine.get('server.port'), 8080)

    def test_set(self):

        logging.info('*** set ***')

        self.engine.set('hello', 'world')
        self.assertEqual(self.engine.get('hello'), 'world')
        self.assertEqual(self.engine.get(u'hello'), 'world')

        self.engine.set('hello', u'wôrld')
        self.assertEqual(self.engine.get('hello'), u'wôrld')

        self.engine.set(u'hello', u'wôrld')
        self.assertEqual(self.engine.get(u'hello'), u'wôrld')

    def test_subscribe(self):

        logging.info('*** subscribe ***')

        with self.assertRaises(AttributeError):
            self.engine.subscribe('*unknown*event', lambda : 'ok')
        with self.assertRaises(AttributeError):
            self.engine.subscribe('bond', lambda : 'ok')
        with self.assertRaises(AttributeError):
            self.engine.subscribe('dispose', lambda : 'ok')

        counter = MyCounter('counter #1')
        with self.assertRaises(AssertionError):
            self.engine.subscribe(None, counter)
        with self.assertRaises(AssertionError):
            self.engine.subscribe('', counter)
        with self.assertRaises(AssertionError):
            self.engine.subscribe(1.2, counter)

        self.engine.subscribe('bond', counter)
        self.engine.subscribe('dispose', counter)

        with self.assertRaises(AttributeError):
            self.engine.subscribe('start', counter)
        with self.assertRaises(AttributeError):
            self.engine.subscribe('stop', counter)
        with self.assertRaises(AttributeError):
            self.engine.subscribe('*unknown*event', counter)

        self.engine.subscribe('bond', MyCounter('counter #2'))

        class AllEvents(object):
            def on_bond(self):
                pass
            def on_dispose(self):
                pass
            def on_start(self):
                pass
            def on_stop(self):
                pass
            def on_message(self):
                pass
            def on_attachment(self):
                pass
            def on_join(self):
                pass
            def on_leave(self):
                pass
            def on_enter(self):
                pass
            def on_exit(self):
                pass
            def on_inbound(self):
                pass
            def on_some_custom_event(self):
                pass

        all_events = AllEvents()
        self.engine.subscribe('bond', all_events)
        self.engine.subscribe('dispose', all_events)
        self.engine.subscribe('start', all_events)
        self.engine.subscribe('stop', all_events)
        self.engine.subscribe('message', all_events)
        self.engine.subscribe('attachment', all_events)
        self.engine.subscribe('join', all_events)
        self.engine.subscribe('leave', all_events)
        self.engine.subscribe('enter', all_events)
        self.engine.subscribe('exit', all_events)
        self.engine.subscribe('inbound', all_events)
        self.engine.subscribe('some_custom_event', all_events)

        self.assertEqual(len(self.engine.subscribed['bond']), 3)
        self.assertEqual(len(self.engine.subscribed['dispose']), 2)
        self.assertEqual(len(self.engine.subscribed['start']), 1)
        self.assertEqual(len(self.engine.subscribed['stop']), 1)
        self.assertEqual(len(self.engine.subscribed['message']), 1)
        self.assertEqual(len(self.engine.subscribed['attachment']), 1)
        self.assertEqual(len(self.engine.subscribed['join']), 1)
        self.assertEqual(len(self.engine.subscribed['leave']), 1)
        self.assertEqual(len(self.engine.subscribed['enter']), 1)
        self.assertEqual(len(self.engine.subscribed['exit']), 1)
        self.assertEqual(len(self.engine.subscribed['inbound']), 1)
        self.assertEqual(len(self.engine.subscribed['some_custom_event']), 1)

    def test_dispatch(self):

        logging.info('*** dispatch ***')

        counter = MyCounter('counter #1')
        self.engine.subscribe('bond', counter)
        self.engine.subscribe('dispose', counter)

        self.engine.subscribe('bond', MyCounter('counter #2'))
        self.engine.subscribe('dispose', MyCounter('counter #3'))

        class AllEvents(object):
            def __init__(self):
                self.events = []
            def on_bond(self):
                self.events.append('bond')
            def on_dispose(self):
                self.events.append('dispose')
            def on_start(self):
                self.events.append('start')
            def on_stop(self):
                self.events.append('stop')
            def on_message(self, received):
                assert received == '*void'
                self.events.append('message')
            def on_attachment(self, received):
                assert received == '*void'
                self.events.append('attachment')
            def on_join(self, received):
                assert received == '*void'
                self.events.append('join')
            def on_leave(self, received):
                assert received == '*void'
                self.events.append('leave')
            def on_enter(self, received):
                assert received == '*void'
                self.events.append('enter')
            def on_exit(self, received):
                assert received == '*void'
                self.events.append('exit')
            def on_inbound(self, received):
                assert received == '*void'
                self.events.append('inbound')
            def on_some_custom_event(self, data):
                assert data == '*data'
                self.events.append('some_custom_event')

        all_events = AllEvents()
        self.engine.subscribe('bond', all_events)
        self.engine.subscribe('dispose', all_events)
        self.engine.subscribe('start', all_events)
        self.engine.subscribe('stop', all_events)
        self.engine.subscribe('message', all_events)
        self.engine.subscribe('attachment', all_events)
        self.engine.subscribe('join', all_events)
        self.engine.subscribe('leave', all_events)
        self.engine.subscribe('enter', all_events)
        self.engine.subscribe('exit', all_events)
        self.engine.subscribe('inbound', all_events)
        self.engine.subscribe('some_custom_event', all_events)

        self.engine.dispatch('bond')
        self.engine.dispatch('dispose')
        self.engine.dispatch('start')
        self.engine.dispatch('stop')
        self.engine.dispatch('message', received='*void')
        self.engine.dispatch('attachment', received='*void')
        self.engine.dispatch('join', received='*void')
        self.engine.dispatch('leave', received='*void')
        self.engine.dispatch('enter', received='*void')
        self.engine.dispatch('exit', received='*void')
        self.engine.dispatch('inbound', received='*void')
        self.engine.dispatch('some_custom_event', data='*data')

        with self.assertRaises(AssertionError):
            self.engine.dispatch('*unknown*event')

        self.assertEqual(counter.count, 2)
        self.assertEqual(all_events.events,
                         ['bond',
                          'dispose',
                          'start',
                          'stop',
                          'message',
                          'attachment',
                          'join',
                          'leave',
                          'enter',
                          'exit',
                          'inbound',
                          'some_custom_event'])

    def test_load_commands(self):

        logging.info('*** load_commands ***')

        with mock.patch.object(self.engine.shell,
                               'load_commands',
                               return_value=None) as mocked:
            self.engine.load_commands(['a', 'b', 'c', 'd'])
            mocked.assert_called_with(['a', 'b', 'c', 'd'])

    def test_hook(self):

        logging.info('*** hook ***')

        self.context.set('server.url', 'http://here.you.go:123')
        server = mock.Mock()
        with mock.patch.object(self.engine.space,
                               'register',
                               return_value=None) as mocked:

            self.engine.hook(server=server)
            self.assertFalse(mocked.called)

            self.context.set('server.binding', '0.0.0.0')
            self.engine.hook(server=server)
            mocked.assert_called_with(hook_url='http://here.you.go:123/hook')

    def test_get_hook(self):

        logging.info('*** get_hook ***')

        self.context.set('server.url', 'http://here.you.go:123')
        self.assertEqual(self.engine.get_hook(), self.engine.space.webhook)

    def test_run(self):

        logging.info('*** run ***')

        engine = Engine(context=self.context)
        engine.space=LocalSpace(engine=engine)

        engine.start = mock.Mock()
        engine.space.run = mock.Mock()

        engine.run()
        self.assertTrue(engine.start.called)
        self.assertTrue(engine.space.run.called)

        class MyServer(object):
            def __init__(self, engine):
                self.engine = engine

            def add_route(self, route, **kwargs):
                pass

            def run(self):
                self.engine.set("has_been_ran", True)

        server = MyServer(engine=engine)
        engine.run(server=server)
        self.assertTrue(engine.get("has_been_ran"))

    def test_start(self):

        logging.info('*** start ***')

        engine = Engine(context=self.context)
        engine.space=LocalSpace(engine=engine)

        engine.start_processes = mock.Mock()
        engine.on_start = mock.Mock()

        engine.start()
        self.assertTrue(engine.ears is not None)
        self.assertTrue(engine.mouth is not None)
        self.assertTrue(engine.start_processes.called)
        self.assertTrue(engine.on_start.called)

    def test_static(self):

        logging.info('*** static test ***')

        self.engine.start()
        time.sleep(0.1)
        self.engine.stop()

        self.assertEqual(self.engine.get('listener.counter', 0), 0)
        self.assertEqual(self.engine.get('speaker.counter', 0), 0)

    def test_enumerate_bots(self):

        logging.info('*** enumerate_bots ***')

        self.engine.bots = {
            '123': FakeBot(self.engine, '123'),
            '456': FakeBot(self.engine, '456'),
            '789': FakeBot(self.engine, '789'),
        }

        for bot in self.engine.enumerate_bots():
            self.assertTrue(bot.space_id in ['123', '456', '789'])

    def test_get_bot(self):

        logging.info('*** get_bot ***')

        self.engine.bots = {
            '123': FakeBot(self.engine, '123'),
            '456': FakeBot(self.engine, '456'),
            '789': FakeBot(self.engine, '789'),
        }

        bot = self.engine.get_bot('123')
        self.assertEqual(bot.space_id, '123')
        self.assertEqual(bot, self.engine.bots['123'])

        bot = self.engine.get_bot('456')
        self.assertEqual(bot.space_id, '456')
        self.assertEqual(bot, self.engine.bots['456'])

        bot = self.engine.get_bot('789')
        self.assertEqual(bot.space_id, '789')
        self.assertEqual(bot, self.engine.bots['789'])

        with mock.patch.object(self.engine,
                               'build_bot',
                               return_value=FakeBot(self.engine, '*bot')) as mocked:

            bot = self.engine.get_bot()
            self.assertEqual(bot.space_id, '*bot')
            self.assertTrue('*bot' in self.engine.bots.keys())

    def test_build_bot(self):

        logging.info('*** build_bot ***')

        self.engine.context.apply(self.engine.DEFAULT_SETTINGS)
        self.engine.bots = {}

        bot = self.engine.build_bot('123', FakeBot)
        self.assertEqual(bot.space_id, '123')
        bot.store.remember('a', 'b')
        self.assertEqual(bot.store.recall('a'), 'b')

        bot = self.engine.build_bot('456', FakeBot)
        self.assertEqual(bot.space_id, '456')
        bot.store.remember('c', 'd')
        self.assertEqual(bot.store.recall('a'), None)
        self.assertEqual(bot.store.recall('c'), 'd')

        bot = self.engine.build_bot('789', FakeBot)
        self.assertEqual(bot.space_id, '789')
        bot.store.remember('e', 'f')
        self.assertEqual(bot.store.recall('a'), None)
        self.assertEqual(bot.store.recall('c'), None)
        self.assertEqual(bot.store.recall('e'), 'f')

    def test_build_space(self):

        logging.info('*** build_space ***')

        self.engine.context.apply(self.engine.DEFAULT_SETTINGS)
        self.engine.context.apply(self.engine.space.DEFAULT_SETTINGS)
        space = self.engine.build_space('123')

    def test_build_store(self):

        logging.info('*** build_store ***')

        store_1 = self.engine.build_store('123')
        store_1.append('names', 'Alice')
        store_1.append('names', 'Bob')
        self.assertEqual(store_1.recall('names'), ['Alice', 'Bob'])

        store_2 = self.engine.build_store('456')
        store_2.append('names', 'Chloe')
        store_2.append('names', 'David')
        self.assertEqual(store_2.recall('names'), ['Chloe', 'David'])

        self.assertEqual(store_1.recall('names'), ['Alice', 'Bob'])
        store_2.forget()
        self.assertEqual(store_1.recall('names'), ['Alice', 'Bob'])
        self.assertEqual(store_2.recall('names'), None)

    def test_initialize_store(self):

        logging.info('*** initialize_store ***')

        settings = {'bot.store': {'planets': ['Uranus', 'Mercury']}}
        self.engine.context.apply(settings)
        print(self.engine.get('bot.store'))
        bot = self.engine.build_bot('123', FakeBot)
        self.assertEqual(bot.store.recall('planets'), ['Uranus', 'Mercury'])

    def test_build_machine(self):

        logging.info('*** build_machine ***')

        bot = ShellBot(engine=self.engine)
        machine = self.engine.build_machine(bot)

        previous = self.engine.machine_factory
        self.engine.machine_factory = MachinesFactory(
            module='shellbot.machines.base',
            name='Machine')
        machine = self.engine.build_machine(bot)
        self.engine.machine_factory = previous

    def test_on_build(self):

        logging.info('*** on_build ***')

        bot = ShellBot(engine=self.engine)
        self.engine.on_build(bot)


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
