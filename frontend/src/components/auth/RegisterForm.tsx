/**
 * 회원가입 폼 컴포넌트
 */
import React, { useState } from 'react';
import { Formik, Form, Field, ErrorMessage, FormikProps } from 'formik';
import * as Yup from 'yup';
import { useAuth } from '../../contexts/AuthContext';
import { RegisterData } from '../../services/auth';

interface RegisterFormValues extends RegisterData {
  confirmPassword: string;
}

const registerSchema = Yup.object().shape({
  email: Yup.string()
    .email('올바른 이메일 주소를 입력해주세요')
    .required('이메일은 필수입니다'),
  username: Yup.string()
    .min(2, '사용자명은 최소 2자 이상이어야 합니다')
    .max(50, '사용자명은 최대 50자까지 가능합니다')
    .required('사용자명은 필수입니다'),
  password: Yup.string()
    .min(6, '비밀번호는 최소 6자 이상이어야 합니다')
    .required('비밀번호는 필수입니다'),
  confirmPassword: Yup.string()
    .oneOf([Yup.ref('password')], '비밀번호가 일치하지 않습니다')
    .required('비밀번호 확인은 필수입니다'),
});

interface RegisterFormProps {
  onSuccess?: () => void;
  onSwitchToLogin?: () => void;
}

export const RegisterForm: React.FC<RegisterFormProps> = ({ 
  onSuccess, 
  onSwitchToLogin 
}) => {
  const { register } = useAuth();
  const [error, setError] = useState<string>('');

  const handleSubmit = async (values: RegisterFormValues) => {
    try {
      setError('');
      const { confirmPassword, ...registerData } = values;
      await register(registerData);
      onSuccess?.();
    } catch (err: any) {
      const errorMessage = err.response?.data?.detail || 
        '회원가입에 실패했습니다. 다시 시도해주세요.';
      setError(errorMessage);
    }
  };  return (
    <div className="max-w-md mx-auto bg-white p-8 rounded-lg shadow-md">
      <h2 className="text-2xl font-bold text-center mb-6 text-gray-800">
        회원가입
      </h2>
      
      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}

      <Formik
        initialValues={{ email: '', username: '', password: '', confirmPassword: '' }}
        validationSchema={registerSchema}
        onSubmit={handleSubmit}
      >
        {(props: FormikProps<RegisterFormValues>) => (
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
                사용자명
              </label>
              <Field
                type="text"
                name="username"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="사용자명을 입력해주세요"
              />
              <ErrorMessage name="username" component="div" className="text-red-500 text-sm mt-1" />
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
            </div>            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                비밀번호 확인
              </label>
              <Field
                type="password"
                name="confirmPassword"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                placeholder="비밀번호를 다시 입력해주세요"
              />
              <ErrorMessage name="confirmPassword" component="div" className="text-red-500 text-sm mt-1" />
            </div>

            <button
              type="submit"
              disabled={props.isSubmitting}
              className="w-full bg-green-600 text-white py-2 px-4 rounded-md hover:bg-green-700 focus:outline-none focus:ring-2 focus:ring-green-500 disabled:opacity-50"
            >
              {props.isSubmitting ? '가입 중...' : '회원가입'}
            </button>
          </Form>
        )}
      </Formik>

      {onSwitchToLogin && (
        <p className="mt-4 text-center text-sm text-gray-600">
          이미 계정이 있으신가요?{' '}
          <button
            type="button"
            onClick={onSwitchToLogin}
            className="text-blue-600 hover:text-blue-800 font-medium"
          >
            로그인
          </button>
        </p>
      )}
    </div>
  );
};