# -*- coding: utf-8 -*-
from __future__ import absolute_import

from django.test.runner import DiscoverRunner
from django.conf import settings

from .registry import TestRequestorRegistry
from .helper import UrlPatternHelper
from .cases import ViewHasRequestorTestCase, RegularViewRequestIsSuccessfulTestCase, \
    AdminViewRequestIsSuccessfulTestCase, RegularUnknownMethodsTestCase, AuthenticationEnforcementTestCase, \
    HeaderKeyExistsTestCase, HeaderValueAccurateTestCase, HeaderKeyNotExistsTestCase, AdminUnknownMethodsTestCase, \
    RegularVerbNotSupportedTestCase, AdminVerbNotSupportedTestCase, CsrfEnforcementTestCase
from .safaker import SaFaker


def get_view_from_callback(callback):
    """
    Get the view associated with the given callback.
    :param callback: The callback to get the view from.
    :return: The view associated with the given callback.
    """
    if hasattr(callback, "view_class"):
        return callback.view_class
    else:
        return callback


class StreetArtTestRunner(DiscoverRunner):
    """
    This is a custom discover runner for populating unit tests for the Street Art project.
    """

    # Class Members

    ALL_HTTP_VERBS = [
        "GET",
        "HEAD",
        "POST",
        "PUT",
        "DELETE",
        "OPTIONS",
        "TRACE",
        "PATCH",
    ]

    CSRF_VERBS = [
        "POST",
        "PUT",
        "DELETE",
        "PATCH",
    ]

    # Instantiation

    def __init__(self, *args, **kwargs):
        self._url_patterns = None
        super(StreetArtTestRunner, self).__init__(*args, **kwargs)

    # Static Methods

    # Class Methods

    # Public Methods

    def build_suite(self, test_labels=None, extra_tests=None, **kwargs):
        """
        Build the test suite to run for this discover runner.
        :param test_labels: A list of strings describing the tests to be run.
        :param extra_tests: A list of extra TestCase instances to add to the suite that is
        executed by the test runner.
        :param kwargs: Additional keyword arguments.
        :return: The test suite.
        """
        extra_tests = extra_tests if extra_tests is not None else []
        extra_tests.extend(self.__get_generated_test_cases())
        return super(StreetArtTestRunner, self).build_suite(
            test_labels=test_labels,
            extra_tests=extra_tests,
            **kwargs
        )

    def run_suite(self, suite, **kwargs):
        """
        Override the run_suite functionality to populate the database.
        :param suite: The suite to run.
        :param kwargs: Keyword arguments.
        :return: The rest suite result.
        """
        self.__populate_database()
        return super(StreetArtTestRunner, self).run_suite(suite, **kwargs)

    # Protected Methods

    # Private Methods

    def __get_authentication_enforcement_tests(self):
        """
        Get a list of test cases that will test whether or not authentication is correctly enforced
        on a given view.
        :return: A list of test cases that will test whether or not authentication is correctly enforced
        on a given view.
        """
        to_return = []
        for _, _, callback in self.url_patterns:
            view, requestor = self.__get_view_and_requestor_from_callback(callback)
            if not requestor.requires_auth:
                continue
            for supported_verb in requestor.supported_verbs:

                class AnonTestCase(AuthenticationEnforcementTestCase):
                    pass

                to_return.append(AnonTestCase(view=view, verb=supported_verb))
        return to_return

    def __get_csrf_enforcement_tests(self):
        """
        Get a list of test cases that check to make sure that CSRF checks are being correctly
        enforced.
        :return: A list of test cases that check to make sure that CSRF checks are being correctly
        enforced.
        """
        to_return = []
        csrf_verbs = [x.lower() for x in self.CSRF_VERBS]
        for _, _, callback in self.url_patterns:
            view, requestor = self.__get_view_and_requestor_from_callback(callback)
            supported_verbs = [x.lower() for x in requestor.supported_verbs]
            supported_csrf_verbs = filter(lambda x: x in csrf_verbs, supported_verbs)
            for supported_csrf_verb in supported_csrf_verbs:

                class AnonTestCase1(CsrfEnforcementTestCase):
                    pass

                to_return.append(AnonTestCase1(view=view, verb=supported_csrf_verb))
        return to_return

    def __get_dos_class_tests(self):
        """
        Get a list of test cases that will test to ensure that all of the configured URL routes
        return successful HTTP status codes.
        :return: A list of test cases that will test to ensure that all of the configured URL routes
        return successful HTTP status codes.
        """
        to_return = []
        for _, _, callback in self.url_patterns:
            view, requestor = self.__get_view_and_requestor_from_callback(callback)
            for supported_verb in requestor.supported_verbs:

                class AnonTestCase1(RegularViewRequestIsSuccessfulTestCase):
                    pass

                class AnonTestCase2(AdminViewRequestIsSuccessfulTestCase):
                    pass

                to_return.append(AnonTestCase1(view=view, verb=supported_verb))
                to_return.append(AnonTestCase2(view=view, verb=supported_verb))
        return to_return

    def __get_generated_test_cases(self):
        """
        Get a list containing the automatically generated test cases to add to the test suite
        this runner is configured to run.
        :return: A list containing the automatically generated test cases to add to the test suite
        this runner is configured to run.
        """

        # Ensure that all views are loaded
        import sectesting.urls

        to_return = []
        if settings.TEST_FOR_REQUESTOR_CLASSES:
            to_return.extend(self.__get_requestor_class_tests())
        if settings.TEST_FOR_DENIAL_OF_SERVICE:
            to_return.extend(self.__get_dos_class_tests())
        if settings.TEST_FOR_UNKNOWN_METHODS:
            to_return.extend(self.__get_unknown_methods_tests())
        if settings.TEST_FOR_AUTHENTICATION_ENFORCEMENT:
            to_return.extend(self.__get_authentication_enforcement_tests())
        if settings.TEST_FOR_RESPONSE_HEADERS:
            to_return.extend(self.__get_response_header_tests())
        if settings.TEST_FOR_OPTIONS_ACCURACY:
            to_return.extend(self.__get_options_accuracy_tests())
        if settings.TEST_FOR_CSRF_ENFORCEMENT:
            to_return.extend(self.__get_csrf_enforcement_tests())
        return to_return

    def __get_options_accuracy_tests(self):
        """
        Get a list of test cases that will test to ensure that no verbs other than those specified
        in OPTIONS responses are present on all views.
        :return: A list of test cases that will test to ensure that no verbs other than those specified
        in OPTIONS responses are present on all views.
        """
        to_return = []
        for _, _, callback in self.url_patterns:
            view, requestor = self.__get_view_and_requestor_from_callback(callback)
            supported_verbs = [x.lower() for x in requestor.supported_verbs]
            for http_verb in self.ALL_HTTP_VERBS:
                if http_verb.lower() not in supported_verbs:

                    class AnonTestCase1(RegularVerbNotSupportedTestCase):
                        pass

                    class AnonTestCase2(AdminVerbNotSupportedTestCase):
                        pass

                    to_return.append(AnonTestCase1(view=view, verb=http_verb))
                    to_return.append(AnonTestCase2(view=view, verb=http_verb))
        return to_return

    def __get_response_header_tests(self):
        """
        Get a list of test cases that will test the views associated with the Street Art project to ensure
        that the expected response headers are found in all responses.
        :return: A list of test cases that will test the views associated with the Street Art project to ensure
        that the expected response headers are found in all responses.
        """
        to_return = []
        for _, _, callback in self.url_patterns:
            view, requestor = self.__get_view_and_requestor_from_callback(callback)
            for k, v in settings.EXPECTED_RESPONSE_HEADERS["included"].iteritems():
                for supported_verb in requestor.supported_verbs:

                    class AnonTestCase1(HeaderKeyExistsTestCase):
                        pass

                    class AnonTestCase2(HeaderValueAccurateTestCase):
                        pass

                    to_return.append(AnonTestCase1(view=view, verb=supported_verb, header_key=k))
                    to_return.append(AnonTestCase2(view=view, verb=supported_verb, header_key=k, header_value=v))
            for excluded_header in settings.EXPECTED_RESPONSE_HEADERS["excluded"]:
                for supported_verb in requestor.supported_verbs:

                    class AnonTestCase3(HeaderKeyNotExistsTestCase):
                        pass

                    to_return.append(AnonTestCase3(view=view, verb=supported_verb, header_key=excluded_header))
        return to_return

    def __get_requestor_class_tests(self):
        """
        Get a list of test cases that will test the views associated with the Street Art project to ensure
        that the view has a requestor class associated with it.
        :return: A list of test cases that will test the views associated with the Street Art project to ensure
        that the view has a requestor class associated with it.
        """
        to_return = []
        for _, _, callback in self.url_patterns:

            class AnonTestCase(ViewHasRequestorTestCase):
                pass

            to_return.append(AnonTestCase(self.__get_view_from_callback(callback)))
        return to_return

    def __get_unknown_methods_tests(self):
        """
        Get a list of test cases that will test whether or not views return the expected HTTP verbs
        through OPTIONS requests.
        :return: A list of test cases that will test whether or not views return the expected HTTP verbs
        through OPTIONS requests.
        """
        to_return = []
        for _, _, callback in self.url_patterns:
            view = self.__get_view_from_callback(callback)

            class AnonTestCase1(RegularUnknownMethodsTestCase):
                pass

            class AnonTestCase2(AdminUnknownMethodsTestCase):
                pass

            to_return.append(AnonTestCase1(view))
            to_return.append(AnonTestCase2(view))
        return to_return

    def __get_view_from_callback(self, callback):
        """
        Get the view associated with the given callback.
        :param callback: The callback to get the view from.
        :return: The view associated with the given callback.
        """
        if hasattr(callback, "view_class"):
            return callback.view_class
        else:
            return callback

    def __get_view_and_requestor_from_callback(self, callback):
        """
        Get a tuple containing (1) the view and (2) the requestor associated with the given URL
        pattern callback.
        :param callback: The URL pattern callback to process.
        :return: A tuple containing (1) the view and (2) the requestor associated with the given URL
        pattern callback.
        """
        registry = TestRequestorRegistry.instance()
        view = self.__get_view_from_callback(callback)
        requestor = registry.get_requestor_for_view(view)
        return view, requestor

    def __populate_database(self):
        """
        Populate the database with dummy database models.
        :return: None
        """
        print("Now populating test database...")
        SaFaker.create_users()

    # Properties

    @property
    def url_patterns(self):
        """
        Get a list of tuples containing (1) the URL pattern regex, (2) the pattern name, and (3) the
        callback function for the views that this runner should generate automated tests for.
        :return: a list of tuples containing (1) the URL pattern regex, (2) the pattern name, and (3) the
        callback function for the views that this runner should generate automated tests for.
        """
        if self._url_patterns is None:
            self._url_patterns = UrlPatternHelper.get_all_streetart_views(
                include_admin_views=settings.INCLUDE_ADMIN_VIEWS_IN_TESTS,
                include_auth_views=settings.INCLUDE_AUTH_VIEWS_IN_TESTS,
                include_generic_views=settings.INCLUDE_GENERIC_VIEWS_IN_TESTS,
                include_contenttype_views=settings.INCLUDE_CONTENTTYPE_VIEWS_IN_TESTS,
            )
        return self._url_patterns

    # Representation and Comparison

    def __repr__(self):
        return "<%s>" % (self.__class__.__name__,)

