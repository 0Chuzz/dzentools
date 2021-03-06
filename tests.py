#!/usr/bin/python2
#vim:fileencoding=utf-8

import unittest
import os.path
import warnings
from mock import Mock

from dzentools import ForegroundColour, DzenString, BarElement, Icon

class ColourTest(unittest.TestCase):
    def test_color_apply(self):
        test_col = ForegroundColour("toast")
        self.assertEqual(test_col("ham"),"^fg(toast)ham^fg()")

    def test_nested(self):
        inner_colour = ForegroundColour("inner")
        outer_colour = ForegroundColour("outer")
        result = outer_colour(inner_colour("nested")+"coloured")+ "no colour"
        self.assertEqual(result, 
            "^fg(outer)^fg(inner)nested^fg(outer)coloured^fg()no colour")

    def test_dynamic_color(self):
        class DynCol(object):
            def __str__(self):
                return "dynamic" 
        test_dyncol = ForegroundColour(DynCol())
        self.assertEqual(str(test_dyncol("")), "^fg(dynamic)^fg()")
    

class DzenStringTest(unittest.TestCase):
    def test_carets(self):
        test_col = DzenString(("tst","test"), "^^^^")
        self.assertEqual(str(test_col),"^tst(test)^^^^^^^^")

    def test_equal_str(self):
        prova = DzenString(('lol', 'arg'), "lil")
        self.assertTrue(prova == "^lol(arg)lil")

    def test_concat(self):
        prova = "^" + DzenString(("lol", "lal")) + "^"
        prova += DzenString(("lil", "lul"))
        self.assertEqual(str(prova),'^^^lol(lal)^^^lil(lul)')

    def test_string_methods(self):
        prova = DzenString("prova")
        try:
            result = ( prova.capitalize() == "Prova",
                       prova.upper() == "PROVA",
                       prova.isalpha()
                     )
        except StandardError:
            self.fail("string methods badly implemented")
        else:
            self.assertTrue(all(result), "results: "+ repr(result))


class BarElementTest(unittest.TestCase):
    def test_fixed_size(self):
        elm = BarElement(size=10)
        elm.update = Mock(return_value="testresult123456")
        self.assertEqual(elm.next(),"testresult")

    def test_update(self):
        def updatefunc(static=[0]):
            static[0] += 1
            return "update("+str(static[0])+")"
        elm = BarElement()
        elm.update = Mock(wraps=updatefunc)
        self.assertEqual(elm.next(),"update(1)")
        self.assertEqual(elm.next(),"update(2)")
        self.assertEqual(elm.next(),"update(3)")
        

    def test_graceful_fail(self):
        def wrongfunc():
            raise StandardError
        elm = BarElement()
        elm.update = wrongfunc
        try:
            failed_update = elm.next()
        except StandardError:
            self.fail("uncaught error, no graceful fail")
        else:
            self.assertTrue("Error" in failed_update)

    def test_iterable(self):
        elm = BarElement()
        def multi_iter(static=["1", "2", "3", None]):
            return static.pop(0)
        elm.update = multi_iter
        self.assertEqual(list(elm), ["1", "2", "3"])

    def test_async_upgrade(self):
        class TestElement(BarElement):
            testout = ["1", "2", "3"]
            test_event = False
            def update(self):
                return self.testout.pop(0)
            def check_update(self):
                return self.test_event
        elm = TestElement()
        self.assertEqual(elm.next(), "1")
        self.assertEqual(elm.next(), "1")
        elm.test_event = True
        self.assertEqual(elm.next(), "2")
        self.assertEqual(elm.next(), "3")
        elm.test_event = False
        self.assertEqual(elm.next(), "3")

    def test_scrolling_spaces(self):
        elm = BarElement(size=10, scroll=1)
        elm.update = lambda: "1234"
        self.assertEqual(elm.next(), "      1234")
        self.assertEqual(elm.next(), "     1234 ")

    def test_scrolling(self):
        elm = BarElement(size=3, scroll=1)
        elm.update = lambda: "1234"
        self.assertEqual(elm.next(), "123")
        self.assertEqual(elm.next(), "234")

    def test_params(self):
        elm = BarElement()
        self.assertEqual(elm.params, {})
        elm = BarElement(params=dict(lol=0))
        self.assertTrue("lol" in elm.params)

    def test_easy_params(self):
        elm = BarElement(dict(lol=0))
        self.assertTrue("lol" in elm.params)

    def test_default_params(self):
        class Tdf(BarElement):
            DEFAULT_PARAMS = dict(defa="lol")
        
        self.assertTrue("defa" not in BarElement().params)
        self.assertTrue("defa" in Tdf().params)

        elm = Tdf(params=dict(nodefa="lul"))
        self.assertTrue("nodefa" not in Tdf().params)
        self.assertTrue("nodefa" in elm.params)

    def test_unicode_output(self):
        elm = BarElement()
        elm.update = lambda: u'garçon'
        try:
            self.assertEqual(elm.next(), u'garçon'.encode('utf-8'))
        except UnicodeError:
            self.fail('error in unicode handling')


class IconTest(unittest.TestCase):
    def setUp(self):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", RuntimeWarning)
            self.ico_basedir = os.tmpnam()
        os.mkdir(self.ico_basedir)
        self.ico_name = "fkicon_dzentools_test.xbm"
        self.ico_path = os.path.join(self.ico_basedir, self.ico_name)
        open(self.ico_path, "w").close()
    
    def tearDown(self):
        os.remove(self.ico_path)
        os.rmdir(self.ico_basedir)

    def test_get_code(self):
        icons = Icon(self.ico_basedir)
        icon = icons.get_icon(self.ico_name)
        self.assertEqual(str(icon), "^i({0})".format(self.ico_path))

    def test_fail_nonexistent(self):
        icons = Icon(self.ico_basedir)
        try:
            icon = icons.get_icon("i_shall_not_exist.xbm")
        except IOError:
            pass
        else:
            self.fail("failed file check!")

    def test_fail_nobasedir(self):
        try:
            icons = Icon("dir_shall_not_exists")
        except IOError:
            pass
        else:
            self.fail("failed directory check!")
        

class GradientTest():#unittest.TestCase):
    def test_gradient_creation(self):
        grad_func = lambda: 0.5
        grad_test = Gradient(((0, 7, 15), (15, 7, 0)), grad_func)
        result = grad_test("^_^")
        self.assertEqual(str(result), "^fg(#777777)^^_^^^fg()")

    def test_out_of_bound_val(self):
        grad_func = lambda: 3.14
        grad_test = Gradient(((0, 7, 15), (15, 7, 0)), grad_func)
        result = grad_test("^_^")
        self.assertEqual(str(result), "^fg(#FF7700)^^_^^^fg()")
        grad_func = lambda: -1.0
        grad_test = Gradient(((0, 7, 15), (15, 7, 0)), grad_func)
        result = grad_test("^_^")
        self.assertEqual(str(result), "^fg(#0077FF)^^_^^^fg()")

    def test_dynamic_gradient(self):
        #XXX check when color value is updated!!! (on init, _call, str?)
        def grad_func(static=[0, 5, 10]):
                return float(static.pop(0))/10
        grad_test = Gradient(((0, 7, 15), (15, 7, 0)), grad_func)
        self.assertEqual(str(grad_test("a")), "^fg(#0077FF)^^_^^^fg()")
        self.assertEqual(str(grad_test("a")), "^fg(#777777)^^_^^^fg()")
        self.assertEqual(str(grad_test("a")), "^fg(#FF7700)^^_^^^fg()") 

    def test_invalid_values(self):
        try:
            Gradient("chiquita", "banana")
        except TypeError:
            pass
        else:
            self.fail("accepting invalid arguments for gradient!")


if __name__ == "__main__":
    unittest.main()
