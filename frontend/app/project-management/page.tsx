'use client';

import { Card, CardContent, CardHeader, CardTitle } from '@/components/common/Card';

export default function ProjectManagementPage() {
  return (
    <div className="p-6">
      <div className="mx-auto max-w-6xl">
        <h1 className="mb-6 text-3xl font-bold text-foreground">项目管理</h1>

        <Card>
          <CardHeader>
            <CardTitle>欢迎使用项目管理</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="py-12 text-center">
              <p className="text-muted-foreground">
                这是一个空白页面，可以在这里添加项目管理功能
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

