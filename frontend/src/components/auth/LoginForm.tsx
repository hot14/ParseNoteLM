import React, { useState } from 'react';
import { Formik, Form, Field, ErrorMessage, FormikProps } from 'formik';
import * as Yup from 'yup';
import { useAuth } from '../../contexts/AuthContext';
import { LoginData } from '../../services/auth';

const loginSchema = Yup.object().shape({
  email: Yup.string()
    .email('올바른 이메일 주소를 입력해주세요')
    .required('이메일은 필수입니다'),
  password: Yup.string()
    .min(6, '비밀번호는 최소 6자 이상이어야 합니다')
    .required('비밀번호는 필수입니다'),
});

interface LoginFormProps {
  onSuccess?: () => void;
  onSwitchToRegister?: () => void;
}

export const LoginForm: React.FC<LoginFormProps> = ({ 
  onSuccess, 
  onSwitchToRegister 
}) => {
  const { login } = useAuth();
  const [error, setError] = useState<string>('');

  const handleSubmit = async (values: LoginData) => {
    try {
      setError('');
      await login(values);
      onSuccess?.();
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 
        '로그인에 실패했습니다. 다시 시도해주세요.';
      setError(errorMessage);
    }
  };

  return (
    <div className="max-w-md mx-auto bg-white p-8 rounded-lg shadow-md">
      <h2 className="text-2xl font-bold text-center mb-6 text-gray-800">
        로그인
      </h2>
      
      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}

      <Formik
        initialValues={{ email: '', password: '' }}
        validationSchema={loginSchema}
        onSubmit={handleSubmit}
      >
        {(props: FormikProps<LoginData>) => (
          <Form className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                이메일
              </label>
              <Field
                type="email"
                name="email"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="이메일을 입력해주세요"
              />
              <ErrorMessage name="email" component="div" className="text-red-500 text-sm mt-1" />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                비밀번호
              </label>
              <Field
                type="password"
                name="password"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="비밀번호를 입력해주세요"
              />
              <ErrorMessage name="password" component="div" className="text-red-500 text-sm mt-1" />
            </div>

            <button
              type="submit"
              disabled={props.isSubmitting}
              className="w-full bg-blue-600 text-white py-2 px-4 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
            >
              {props.isSubmitting ? '로그인 중...' : '로그인'}
            </button>
          </Form>
        )}
      </Formik>

      {onSwitchToRegister && (
        <p className="mt-4 text-center text-sm text-gray-600">
          계정이 없으신가요?{' '}
          <button
            type="button"
            onClick={onSwitchToRegister}
            className="text-blue-600 hover:text-blue-800 font-medium"
          >
            회원가입
          </button>
        </p>
      )}
    </div>
  );
};
