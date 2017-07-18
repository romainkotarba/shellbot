#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import gc
import logging
from multiprocessing import Process
import os
import random
import sys
import time

from shellbot import Context


class ContextTests(unittest.TestCase):

    def setUp(self):
        self.context = Context()

    def tearDown(self):
        del self.context
        collected = gc.collect()
        if collected:
            logging.info("Garbage collector: collected %d objects." % (collected))

    def test_init(self):

        settings = {
            'bot': {'name': 'testy', 'version': '17.4.1'},
        }

        self.context = Context(settings)
        self.assertEqual(self.context.get('bot.name'), 'testy')
        self.assertEqual(self.context.get('bot.version'), '17.4.1')

    def test_init_filter(self):

        self.context = Context(filter=lambda x, y : x + '...')
        self.context.apply({'my.var': 'my value'})
        self.context.check('my.var', filter=True)
        self.assertEqual(self.context.get('my.var'), 'my value...')

    def test_apply(self):

        self.assertEqual(self.context.get('general.port'), None)

        settings = {
            'spark': {'CISCO_SPARK_BTTN_BOT': 'who_knows'},
            'spark.room': 'title',
            'DEBUG': True,
            'server': {'port': 80, 'url': 'http://www.acme.com/'},
            'bot.store': {'planets': ['Uranus', 'Mercury']},
        }

        self.context.apply(settings)

        self.assertEqual(self.context.get('general.DEBUG'), True)
        self.assertEqual(self.context.get('spark.CISCO_SPARK_BTTN_BOT'),
                         'who_knows')
        self.assertEqual(self.context.get('spark.room'), 'title')
        self.assertEqual(self.context.get('server.port'), 80)
        self.assertEqual(self.context.get('server.url'),
                         'http://www.acme.com/')
        self.assertEqual(self.context.get('bot.store.planets'),
                         ['Uranus', 'Mercury'])
        self.assertEqual(self.context.get('bot.store'),
                         {'planets': ['Uranus', 'Mercury']})

    def test_clear(self):

        self.assertEqual(self.context.get('general.port'), None)

        settings = {
            'spark': {'CISCO_SPARK_BTTN_BOT': 'who_knows'},
            'spark.room': 'title',
            'DEBUG': True,
            'server': {'port': 80, 'url': 'http://www.acme.com/'},
        }

        self.context.apply(settings)

        self.assertEqual(self.context.get('general.DEBUG'), True)
        self.assertEqual(self.context.get('spark.CISCO_SPARK_BTTN_BOT'),
                         'who_knows')
        self.assertEqual(self.context.get('spark.room'), 'title')
        self.assertEqual(self.context.get('server.port'), 80)
        self.assertEqual(self.context.get('server.url'), 'http://www.acme.com/')

        self.context.clear()

        self.assertEqual(self.context.get('general.DEBUG'), None)
        self.assertEqual(self.context.get('spark.CISCO_SPARK_BTTN_BOT'), None)
        self.assertEqual(self.context.get('spark.room'), None)
        self.assertEqual(self.context.get('server.port'), None)
        self.assertEqual(self.context.get('server.url'), None)

    def test_is_empty(self):

        self.assertTrue(self.context.is_empty)

        # set a key
        self.context.set('hello', 'world')
        self.assertEqual(self.context.get('hello'), 'world')
        self.assertFalse(self.context.is_empty)

        self.context.clear()
        self.assertTrue(self.context.is_empty)

        settings = {
            'spark': {'CISCO_SPARK_BTTN_BOT': 'who_knows'},
            'spark.room': 'title',
            'DEBUG': True,
            'server': {'port': 80, 'url': 'http://www.acme.com/'},
        }

        self.context.apply(settings)
        self.assertFalse(self.context.is_empty)

    def test_check(self):

        self.assertEqual(self.context.get('spark.room'), None)

        settings = {
            'spark': {
                'room': 'My preferred room',
                'moderators':
                    ['foo.bar@acme.com', 'joe.bar@corporation.com'],
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                'team': 'Anchor team',
                'token': 'hkNWEtMJNkODk3ZDZLOGQ0OVGlZWU1NmYtyY',
                'personal_token': '$MY_FUZZY_SPARK_TOKEN',
                'fuzzy_token': '$MY_FUZZY_SPARK_TOKEN',
                'webhook': "http://73a1e282.ngrok.io",
            }
        }

        self.context.apply(settings)

        self.context.check('spark.room', is_mandatory=True)
        self.assertEqual(self.context.get('spark.room'), 'My preferred room')

        self.context.check('spark.team')
        self.assertEqual(self.context.get('spark.team'), 'Anchor team')

        self.context.check('spark.*not*present')   # will be set to None
        self.assertEqual(self.context.get('spark.*not*present'), None)

        self.context.check('spark.absent_list', default=[])
        self.assertEqual(self.context.get('spark.absent_list'), [])

        self.context.check('spark.absent_dict', default={})
        self.assertEqual(self.context.get('spark.absent_dict'), {})

        self.context.check('spark.absent_text', default='*born')
        self.assertEqual(self.context.get('spark.absent_text'), '*born')

        # is_mandatory is useless if default is set
        self.context.check('spark.*not*present',
                         default='*born',
                         is_mandatory=True)
        self.assertEqual(self.context.get('spark.*not*present'), '*born')

        # missing key
        with self.assertRaises(KeyError):
            self.context.check('spark.*unknown*key*',
                             is_mandatory=True)

        # validate implies is_mandatory
        with self.assertRaises(KeyError):
            self.context.check('spark.*unknown*key*',
                             validate=lambda line: True)

        # filter does imply is_mandatory
        with self.assertRaises(KeyError):
            self.context.check('spark.*unknown*key*',
                             filter=True)

        self.context.check('spark.webhook',
                         validate=lambda line: line.startswith('http'))
        self.assertEqual(self.context.get('spark.webhook'),
                         "http://73a1e282.ngrok.io")

        with self.assertRaises(ValueError):
            self.context.check('spark.token',
                             validate=lambda line: len(line) == 32)
        self.assertEqual(self.context.get('spark.token'),
                         'hkNWEtMJNkODk3ZDZLOGQ0OVGlZWU1NmYtyY')

        self.context.check('spark.personal_token')
        self.assertEqual(self.context.get('spark.personal_token'),
                         '$MY_FUZZY_SPARK_TOKEN')

        self.context.check('spark.personal_token', filter=True)  # warning in log
        self.assertEqual(self.context.get('spark.personal_token'),
                         None)

        self.context.apply(settings)

        os.environ['MY_FUZZY_SPARK_TOKEN'] = ''
        self.context.check('spark.personal_token', filter=True)
        self.assertEqual(self.context.get('spark.personal_token'), '')

        self.context.check('spark.fuzzy_token')
        self.assertEqual(self.context.get('spark.fuzzy_token'),
                         '$MY_FUZZY_SPARK_TOKEN')

        os.environ['MY_FUZZY_SPARK_TOKEN'] = 'hello'
        self.context.check('spark.fuzzy_token', filter=True)
        self.assertEqual(self.context.get('spark.fuzzy_token'), 'hello')

    def test__filter(self):

        self.assertEqual(Context._filter(None), None)

        self.assertEqual(Context._filter(''), '')

        self.assertEqual(Context._filter('ZLOGQ0OVGlZWU1NmYtyY'),
                         'ZLOGQ0OVGlZWU1NmYtyY')

        if os.environ.get('PATH') is not None:
            self.assertTrue(Context._filter('$PATH') != '$PATH')

        Context._filter('$TOTALLY*UNKNOWN*HERE')  # warning in log

    def test_has(self):

        self.context.apply({
            'spark': {
                'room': 'My preferred room',
                'moderators':
                    ['foo.bar@acme.com', 'joe.bar@corporation.com'],
                'participants':
                    ['alan.droit@azerty.org', 'bob.nard@support.tv'],
                'team': 'Anchor team',
                'token': 'hkNWEtMJNkODk3ZDZLOGQ0OVGlZWU1NmYtyY',
                'personal_token': '$MY_FUZZY_SPARK_TOKEN',
                'fuzzy_token': '$MY_FUZZY_SPARK_TOKEN',
                'webhook': "http://73a1e282.ngrok.io",
            }
        })

        # undefined prefix
        self.assertFalse(self.context.has('hello'))

        # top-level prefix
        self.assertTrue(self.context.has('spark'))

        # 2-level prefix
        self.assertTrue(self.context.has('spark.team'))

        # undefined 2-level prefix
        self.assertFalse(self.context.has('.token'))

    def test_getter(self):

        # undefined key
        self.assertEqual(self.context.get('hello'), None)

        # undefined key with default value
        whatever = 'whatever'
        self.assertEqual(self.context.get('hello', whatever), whatever)

        # set a key
        self.context.set('hello', 'world')
        self.assertEqual(self.context.get('hello'), 'world')

        # default value is meaningless when key has been set
        self.assertEqual(self.context.get('hello', 'whatever'), 'world')

        # except when set to None
        self.context.set('special', None)
        self.assertEqual(self.context.get('special', []), [])

    def test_unicode(self):

        self.context.set('hello', 'world')
        self.assertEqual(self.context.get('hello'), 'world')
        self.assertEqual(self.context.get(u'hello'), 'world')

        self.context.set('hello', u'wôrld')
        self.assertEqual(self.context.get('hello'), u'wôrld')

        self.context.set(u'hello', u'wôrld')
        self.assertEqual(self.context.get(u'hello'), u'wôrld')

    def test_increment(self):

        self.assertEqual(self.context.get('gauge'), None)
        value = self.context.increment('gauge')
        self.assertEqual(value, 1)

        self.context.set('gauge', 'world')
        self.assertEqual(self.context.get('gauge'), 'world')
        value = self.context.increment('gauge')
        self.assertEqual(value, 1)

    def test_decrement(self):

        self.assertEqual(self.context.get('gauge'), None)
        value = self.context.decrement('gauge')
        self.assertEqual(value, -1)

        self.context.set('gauge', 'world')
        self.assertEqual(self.context.get('gauge'), 'world')
        value = self.context.decrement('gauge')
        self.assertEqual(value, -1)

    def test_gauge(self):

        # undefined key
        self.assertEqual(self.context.get('gauge'), None)

        # see if type mismatch would create an error
        self.context.set('gauge', 'world')
        self.assertEqual(self.context.get('gauge'), 'world')

        # increment and decrement the counter
        value = self.context.increment('gauge')
        self.assertEqual(value, 1)
        self.assertEqual(self.context.get('gauge'), 1)

        self.assertEqual(self.context.decrement('gauge', 2), -1)

        self.assertEqual(self.context.increment('gauge', 4), 3)
        self.assertEqual(self.context.decrement('gauge', 10), -7)
        self.assertEqual(self.context.increment('gauge', 27), 20)
        self.assertEqual(self.context.get('gauge'), 20)

        # default value is meaningless when key has been set
        self.assertEqual(self.context.get('gauge', 'world'), 20)

        # reset the gauge
        self.context.set('gauge', 123)
        self.assertEqual(self.context.get('gauge'), 123)

    def test_concurrency(self):

        def worker(id, context):
            for i in range(4):
                r = random.random()
                time.sleep(r)
                value = context.increment('gauge')
                logging.info('worker %d:counter=%d' % (id, value))
            logging.info('worker %d:done' % id)

        logging.info('Creating a counter')
        self.counter = Context()

        logging.info('Launching incrementing workers')
        workers = []
        for i in range(4):
            p = Process(target=worker, args=(i, self.counter,))
            p.start()
            workers.append(p)

        logging.info('Waiting for worker threads')
        for p in workers:
            p.join()

        logging.info('Counter: %d' % self.counter.get('gauge'))
        self.assertEqual(self.counter.get('gauge'), 16)


if __name__ == '__main__':

    Context.set_logger()
    sys.exit(unittest.main())
